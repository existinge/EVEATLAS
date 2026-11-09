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
// Runs JapaneseSplatCity.Editor.ProjectAuthor.Run() first (idempotent authoring
// of the URP pipeline, the WalkMain scene and the EditorBuildSettings entry),
// then fails loudly (non-zero batchmode exit) if the walk scene still does not
// exist or the player build does not succeed.
using System;
using System.IO;
using JapaneseSplatCity.Editor;
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
            // Idempotent offline authoring: URP pipeline assets + global-settings
            // registration, WalkMain.unity, build-scene entry (see ProjectAuthor.cs).
            ProjectAuthor.Run();

            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) == null)
            {
                throw new InvalidOperationException(
                    "Build aborted: scene not found at " + ScenePath +
                    " AFTER ProjectAuthor.Run() — check Console for authoring errors " +
                    "(URP package import state) and retry.");
            }

            // org.nesnausk.gaussian-splatting REQUIRES IL2CPP: its native plugin
            // loader refuses the Mono runtime. Make the backend explicit so a
            // Mono build can never be produced by accident.
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Standalone, ScriptingImplementation.IL2CPP);
            if (PlayerSettings.GetScriptingBackend(BuildTargetGroup.Standalone) != ScriptingImplementation.IL2CPP)
            {
                throw new InvalidOperationException(
                    "Build aborted: scripting backend is not IL2CPP for Standalone " +
                    "(required by the Gaussian Splatting package).");
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
