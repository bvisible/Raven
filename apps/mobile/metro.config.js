const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const path = require('path');

// Find the project and workspace directories
const projectRoot = __dirname;
// This can be replaced with `find-yarn-workspace-root`
const monorepoRoot = path.resolve(projectRoot, '../..');

module.exports = (() => {
    const config = getDefaultConfig(projectRoot);

    // Extract existing transformer and resolver
    const { transformer, resolver } = config;

    //// Neoffice - Metro watch folders (17fbaed07, 2026-01-20 "fix: metro watchFolders and version
    //// bump 1.1.4"): upstream REPLACES the default watchFolders with the monorepo root, which dropped
    //// the folders Expo adds itself and broke hot reload on our layout. Extend the list instead.
    // 1. Watch all files within the monorepo (extend default watchFolders)
    config.watchFolders = [...(config.watchFolders || []), monorepoRoot];

    // Add SVG transformer configuration
    config.transformer = {
        ...transformer,
        babelTransformerPath: require.resolve("react-native-svg-transformer/expo"),
    };

    config.resolver = {
        ...resolver,
        assetExts: resolver.assetExts.filter((ext) => ext !== "svg"),
        sourceExts: [...resolver.sourceExts, "svg"],
        nodeModulesPaths: [path.resolve(projectRoot, 'node_modules'), path.resolve(monorepoRoot, 'node_modules')],
    };

    // Wrap the updated config with NativeWind and add options
    return withNativeWind(config, {
        input: "./global.css",
        inlineRem: 16,
    });
})();
