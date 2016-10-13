const tern = require('tern');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const resolveFrom = require('resolve-from');

const distDir = path.resolve(__dirname, path.join('node_modules', 'tern'));
var projectDir = process.cwd();

const rl = readline.createInterface({
  input: process.stdin,
  output: null,
  historySize: 0,
  terminal: false
});

const defaultConfig = {
  libs: [],
  plugins: {doc_comment: true},
  ecmaScript: true,
  ecmaVersion: 6,
  dependencyBudget: tern.defaultOptions.dependencyBudget
};

function mergeObjects(base, value) {
  if (!base) return value;
  if (!value) return base;
  var result = {};
  for (var prop in base) result[prop] = base[prop];
  for (var prop in value) result[prop] = value[prop];
  return result;
}

function findFile(file, projectDir, fallbackDir) {
  var local = path.resolve(projectDir, file);
  if (fs.existsSync(local)) return local;
  var shared = path.resolve(fallbackDir, file);
  if (fs.existsSync(shared)) return shared;
}

function readJson(fileName) {
  try {
    return JSON.parse(fs.readFileSync(fileName, 'utf8'));
  } catch (e) {
    return null;
  }
}

function findDefs(projectDir, config) {
  var defs = [], src = config.libs.slice();
  if (config.ecmaScript && src.indexOf('ecmascript') == -1) {
    src.unshift('ecmascript');
  }
  for (var i = 0; i < src.length; ++i) {
    var file = src[i];
    if (!/\.json$/.test(file)) file = file + '.json';
    var found = findFile(file, projectDir, path.resolve(distDir, 'defs'))
        || resolveFrom(projectDir, 'tern-' + src[i]);
    if (!found) {
      try {
        found = require.resolve('tern-' + src[i]);
      } catch (e) {
        continue;
      }
    }
    if (found) {
      let def = readJson(found);
      if (def) {
        defs.push(def);
      }
    }
  }
  return defs;
}

function loadPlugins(projectDir, config) {
  var plugins = config.plugins, options = {};
  for (var plugin in plugins) {
    var val = plugins[plugin];
    if (!val) continue;
    var found = findFile(plugin + '.js', projectDir, path.resolve(distDir, 'plugin'))
        || resolveFrom(projectDir, 'tern-' + plugin);
    if (!found) {
      try {
        found = require.resolve('tern-' + plugin);
      } catch (e) {
        continue;
      }
    }
    try {
      var mod = require(found);
      if (mod.hasOwnProperty('initialize')) mod.initialize(distDir);
    } catch (e) {
      continue;
    }
    options[path.basename(plugin)] = val;
  }

  return options;
}

const config = (function(){
  if (process.argv.length >= 3) {
    projectDir = process.argv[2];
    let data = readJson(path.join(projectDir, '.tern-project'));
    if (data) {
      for (var o in defaultConfig) {
        if (!data.hasOwnProperty(o)) {
          data[o] = defaultConfig[o];
        } else if (o == 'plugins') {
          data[o] = mergeObjects(defaultConfig[o], data[o]);
        }
      }
      return data;
    }
  }
  return defaultConfig;
})();

const server = new tern.Server({
  async: true,
  plugins: loadPlugins(projectDir, config),
  defs: findDefs(projectDir, config),
  ecmaVersion: config.ecmaVersion,
  dependencyBudget: config.dependencyBudget,
});

rl.on('line', function(line) {
  try {
    var input = JSON.parse(line);
    get_completions(input.filename, input.line, input.col, input.content);
  } catch (e) {
    console.log(JSON.stringify([]));
  }
});

function get_completions(filename, line, col, data) {
  var query = {
    type: 'completions',
    types: true,
    docs: true,
    file: '#0',
    filter: true,
    expandWordForward: false,
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
      const completion = res.completions[i];
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
