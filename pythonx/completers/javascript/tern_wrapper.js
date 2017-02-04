#!/usr/bin/env node

var fs = require('fs');
var glob = require('glob');
var minimatch = require('minimatch');
var path = require('path');
var readline = require('readline');
var resolveFrom = require('resolve-from');
var tern = require('tern');

var DIST_DIR = path.resolve(__dirname, path.join('node_modules', 'tern'));
var PROJECT_FILE_NAME = '.tern-project';
var PROJECT_DIR = (function() {
  var dir = process.cwd();
  while (true) {
    try {
      if (fs.statSync(path.resolve(dir, PROJECT_FILE_NAME)).isFile()) {
        return dir;
      }
    } catch(e) {}
    var shorter = path.dirname(dir);
    if (shorter == dir) {
      return process.cwd();
    }
    dir = shorter;
  }
})();


function genConfig() {
  var defaultConfig = {
    libs: [],
    loadEagerly: false,
    plugins: {doc_comment: true},
    ecmaScript: true,
    ecmaVersion: 6,
    dependencyBudget: tern.defaultOptions.dependencyBudget
  };

  function merge(base, value) {
    if (!base) return value;
    if (!value) return base;
    var result = {};
    for (var prop in base) result[prop] = base[prop];
    for (var prop in value) result[prop] = value[prop];
    return result;
  }

  function readConfig(fileName) {
    var data = readJSON(fileName);
    for (var option in defaultConfig) {
      if (!data.hasOwnProperty(option))
        data[option] = defaultConfig[option];
      else if (option == 'plugins')
        data[option] = merge(defaultConfig[option], data[option]);
    }
    return data;
  }

  var home = process.env.HOME || process.env.USERPROFILE;
  if (home && fs.existsSync(path.resolve(home, '.tern-config'))) {
    defaultConfig = readConfig(path.resolve(home, '.tern-config'));
  }

  var projectFile = path.resolve(PROJECT_DIR, PROJECT_FILE_NAME);
  if (fs.existsSync(projectFile)) {
    return readConfig(projectFile);
  }

  return defaultConfig;
}


function readJSON(fileName) {
  var file = fs.readFileSync(fileName, 'utf8');
  try {
    return JSON.parse(file);
  } catch (e) {
    console.error('Bad JSON in ' + fileName + ': ' + e.message);
    process.exit(1);
  }
}


function findFile(file, projectDir, fallbackDir) {
  var local = path.resolve(projectDir, file);
  if (fs.existsSync(local)) return local;
  var shared = path.resolve(fallbackDir, file);
  if (fs.existsSync(shared)) return shared;
}


function findDefs(projectDir, config) {
  var defs = [], src = config.libs.slice();
  if (config.ecmaScript && src.indexOf('ecmascript') == -1) {
    src.unshift('ecmascript');
  }
  for (var i = 0; i < src.length; ++i) {
    var file = src[i];
    if (!/\.json$/.test(file)) file = file + '.json';
    var found = findFile(file, projectDir, path.resolve(DIST_DIR, 'defs'))
        || resolveFrom(projectDir, 'tern-' + src[i]);
    if (!found) {
      try {
        found = require.resolve('tern-' + src[i]);
      } catch (e) {
        process.stderr.write('Failed to find library ' + src[i] + '.\n');
        continue;
      }
    }
    if (found) defs.push(readJSON(found));
  }
  return defs;
}


function loadPlugins(projectDir, config) {
  var plugins = config.plugins, options = {};
  for (var plugin in plugins) {
    var val = plugins[plugin];
    if (!val) continue;
    var found = findFile(plugin + '.js', projectDir, path.resolve(DIST_DIR, 'plugin'))
        || resolveFrom(projectDir, 'tern-' + plugin);
    if (!found) {
      try {
        found = require.resolve('tern-' + plugin);
      } catch (e) {
        process.stderr.write('Failed to find plugin ' + plugin + '.\n');
        continue;
      }
    }
    var mod = require(found);
    if (mod.hasOwnProperty('initialize')) mod.initialize(DIST_DIR);
    options[path.basename(plugin)] = val;
  }

  return options;
}


function startServer(dir, config) {
  var defs = findDefs(dir, config);
  var plugins = loadPlugins(dir, config);
  var server = new tern.Server({
    getFile: function(name, c) {
      if (config.dontLoad && config.dontLoad.some(function(pat) { return minimatch(name, pat); })) {
        c(null, '');
      } else {
        fs.readFile(path.resolve(dir, name), 'utf8', c);
      }
    },
    normalizeFilename: function(name) {
      var pt = path.resolve(dir, name);
      try {
        pt = fs.realPathSync(path.resolve(dir, name), true);
      } catch(e) {}
      return path.relative(dir, pt);
    },
    async: true,
    defs: defs,
    plugins: plugins,
    projectDir: dir,
    ecmaVersion: config.ecmaVersion,
    dependencyBudget: config.dependencyBudget,
  });

  if (config.loadEagerly) config.loadEagerly.forEach(function(pat) {
    glob.sync(pat, { cwd: dir }).forEach(function(file) {
      server.addFile(file);
    });
  });
  return server;
}


(function() {
  var server = startServer(PROJECT_DIR, genConfig());

  function complete(filename, line, col, data) {
    var query = {
      type: 'completions',
      types: true,
      guess: false,
      docs: true,
      file: '#0',
      filter: true,
      expandWordForward: false,
      inLiteral: false,
      end: {line: line, ch: col},
    };
    var file = {
      type: 'full',
      name: filename,
      text: data,
    };
    var doc = {query: query, files: [file]};
    server.request(doc, function(err, res) {
      var info = [];
      for (var i = 0; i < res.completions.length; i++) {
        var completion = res.completions[i];
        var comp = {word: completion.name, menu: completion.type};

        if (completion.guess) {
          comp.menu += ' ' + completion.guess;
        }

        if (completion.doc) {
          comp.info = completion.doc;
        }

        info.push(comp);
      }
      console.log(JSON.stringify(info));
    });
  }

  readline.createInterface({
    input: process.stdin,
    output: null,
    historySize: 0,
    terminal: false
  })
  .on('line', function(line) {
    try {
      var input = JSON.parse(line);
      complete(input.filename, input.line, input.col, input.content);
    } catch (e) {
      console.log(JSON.stringify([]));
    }
  });
})();
