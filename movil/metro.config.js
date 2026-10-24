// Los tokens (design/tokens.json) y Chaski (avatar/) viven fuera de movil/ y se importan de ahí,
// sin copias: si cambian en el repo, la app los toma en el siguiente build.
const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
config.watchFolders = [path.resolve(__dirname, '../design'), path.resolve(__dirname, '../avatar')];
module.exports = config;
