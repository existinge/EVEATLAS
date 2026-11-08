// Japanese Splat City — CLI standalone build entry point (Windows x64).
//
// DRAFT, NOT YET COMPILED: requires the first editor import to succeed on a
// licensed machine (this environment is blocked by binary-identity
// confinement). Standard Unity 6000.3 Editor API only; verify with an editor
// compile before trusting it.
//
// Invoked from the command line via Build.ps1, or manually:
//   Unity.exe -batchmode -quit -nographics -projectPath <proj> \
//     -executeMethod JapaneseSplatCity.Build.PlayerBuilder.Build \
//     -outputPath <out>\JapaneseSplatCity.exe
//
// Fails loudly (non-zero batchmode exit) if the walk scene is missing, which
// enforces the "author scene in the editor first" ordering.
using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace JapaneseSplatCity.Build
{
    public static class PlayerBuilder
    {
        const string ScenePath = "Assets/Scenes/WalkMain.unity";

        public static void Build()
        {
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) == null)
            {
                throw new InvalidOperationException(
                    "Build aborted: scene not found at " + ScenePath + " — " +
                    "author the walk scene in the editor and save it there first.");
            }

            string output = GetArg("-outputPath")
                ?? Path.Combine("Build", "JapaneseSplatCity", "JapaneseSplatCity.exe");
            output = Path.GetFullPath(output);

            var options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = output,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.CompressWithLz4HC
            };

            BuildReport report = BuildPipeline.BuildPlayer(options);
            BuildSummary summary = report.summary;
            if (summary.result != BuildResult.Succeeded)
            {
                throw new InvalidOperationException(
                    "Build failed: result=" + summary.result +
                    " totalErrors=" + summary.totalErrors +
                    " output=" + summary.outputPath);
            }

            Debug.Log("[PlayerBuilder] BUILD OK -> " + summary.outputPath +
                " | size=" + summary.totalSize + " bytes | time=" + summary.totalTime);
        }

        static string GetArg(string name)
        {
            string[] args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == name) return args[i + 1];
            }
            return null;
        }
    }
}
