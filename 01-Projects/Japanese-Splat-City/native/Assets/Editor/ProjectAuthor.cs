// Japanese Splat City — offline-first project authoring (DRAFT: requires the FIRST LICENSED
// editor run; not compiled on the license-blocked authoring host — commit-time status is
// "uncompiled, self-contained, review by first import").
//
// Contract: is fully idempotent (every step first checks whether its artifact exists),
// is invoked automatically at the head of PlayerBuilder.Build() AND from a menu item,
// and creates everything a fresh clone of this repo needs on its very first import:
//
//   1. URP pipeline assets under Assets/Settings/:
//        JSC-URP-Renderer.asset  (UniversalRendererData)
//        JSC-URP.asset           (UniversalRenderPipelineAsset with that default renderer)
//      The GaussianSplatURPFeature of the vendored org.nesnausk.gaussian-splatting package is
//      INTERNAL, so it is instantiated by reflection and added via
//      ScriptableRendererData.rendererFeatures. NO manual GS_ENABLE_URP define: the package
//      asmdef declares a versionDefine that flips it automatically because URP 17.3.0 is in
//      native/Packages/manifest.json. If the feature type is missing, that define/package
//      compile state is the problem — the tool fails loudly instead of pretending.
//   2. GraphicsSettings.defaultRenderPipeline = JSC-URP.asset, plus the URP global-settings
//      registration step (reflection over the URP editor class; best effort, non-fatal) so
//      m_RenderPipelineGlobalSettingsMap and the shader-variant collection resolve.
//   3. Assets/Scenes/WalkMain.unity with EXACTLY the minimal root set (per Round-7 design):
//        BlockBuilder   — owns geometry AND PlayerRig/FpsController/Camera/CharacterController
//                         (do NOT author player objects here; BuildPlayer creates them)
//        EvidenceDriver — adds FpsAndCapture to the rig at runtime
//        SplatAnchor    — top-level GO so BlockBuilder.PlaceSplatAnchor finds it by name;
//                         carries the GaussianSplatRenderer bound to m_SourcePath
//                         "M1Anchor_train.ply" (staged into Assets/StreamingAssets by
//                         Build.ps1 step 1/4 from the SHA-verified 266,542,260 B payload;
//                         .gitignore'd *.ply keeps the 266 MB binary out of git).
//      A global Volume carries the fog profile (component resolved by name — it moved
//      assemblies between URP versions; non-fatal if absent).
//   4. EditorBuildSettings entry for WalkMain.unity, satisfying PlayerBuilder's scene gate.
//
// What this deliberately does NOT do: compile check shaders, run the player, or claim any
// URP runtime acceptance — those still need the licensed first import + a packaged run.

using System;
using System.Collections.Generic;
using System.Reflection;
using GaussianSplatting.Runtime;
using JapaneseSplatCity.Block;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace JapaneseSplatCity.Editor
{
    public static class ProjectAuthor
    {
        const string kRendererPath = "Assets/Settings/JSC-URP-Renderer.asset";
        const string kUrpPath = "Assets/Settings/JSC-URP.asset";
        const string kFogProfilePath = "Assets/Settings/JSC-VolumeProfile.asset";
        const string kScenePath = "Assets/Scenes/WalkMain.unity";
        const string kSplatSource = "M1Anchor_train.ply"; // relative to StreamingAssets

        [MenuItem("Japanese Splat City/Author Project (URP + Scene)")]
        public static void Run()
        {
            Debug.Log("[ProjectAuthor] start");
            EnsureFolders();
            UniversalRendererData rd = EnsureUrpRendererData();
            UniversalRenderPipelineAsset urp = EnsureUrpAsset(rd);
            EnsureGraphicsSettings(urp);
            VolumeProfile fog = EnsureFogProfile();
            EnsureScene(fog);
            EnsureBuildSettings();
            AssetDatabase.SaveAssets();
            Debug.Log("[ProjectAuthor] done — URP active on " + kScenePath +
                      ", scene registered in EditorBuildSettings, splat source '" + kSplatSource + "'");
        }

        // ------------------------------------------------------------------ folders

        static void EnsureFolders()
        {
            EnsureFolder("Assets", "Settings");
            EnsureFolder("Assets", "Scenes");
        }

        static void EnsureFolder(string parent, string child)
        {
            string path = parent + "/" + child;
            if (AssetDatabase.IsValidFolder(path)) return;
            AssetDatabase.CreateFolder(parent, child);
            Debug.Log("[ProjectAuthor] created folder " + path);
        }

        // ------------------------------------------------------------------ URP renderer data + splat feature

        static UniversalRendererData EnsureUrpRendererData()
        {
            var rd = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(kRendererPath);
            if (rd != null)
            {
                Debug.Log("[ProjectAuthor] renderer data exists: " + kRendererPath);
                return rd;
            }

            rd = ScriptableObject.CreateInstance<UniversalRendererData>();
            rd.name = "JSC-URP-Renderer";
            AssetDatabase.CreateAsset(rd, kRendererPath);

            ScriptableRendererFeature feature = CreateGaussianSplatFeature();
            rd.rendererFeatures.Add(feature);
            AssetDatabase.AddObjectToAsset(feature, rd);
            EditorUtility.SetDirty(rd);
            Debug.Log("[ProjectAuthor] created " + kRendererPath + " with " + feature.GetType().Name);
            return rd;
        }

        static ScriptableRendererFeature CreateGaussianSplatFeature()
        {
            // Internal type — instantiate by reflection (needs the GS_ENABLE_URP versionDefine
            // active; it is auto-declared by the package asmdef when URP is in the manifest).
            Type t = Type.GetType("GaussianSplatting.Runtime.GaussianSplatURPFeature, GaussianSplatting");
            if (t == null)
            {
                throw new InvalidOperationException(
                    "[ProjectAuthor] GaussianSplatURPFeature not found in assembly 'GaussianSplatting'. " +
                    "The vendored package did not compile with GS_ENABLE_URP (URP 17.3.0 must resolve; " +
                    "check Console for package compile errors), or the package is not imported.");
            }
            var feature = ScriptableObject.CreateInstance(t) as ScriptableRendererFeature;
            if (feature == null)
            {
                throw new InvalidOperationException(
                    "[ProjectAuthor] CreateInstance(" + t.FullName + ") did not yield a ScriptableRendererFeature.");
            }
            feature.name = "Gaussian Splatting";
            return feature;
        }

        // ------------------------------------------------------------------ URP pipeline asset

        static UniversalRenderPipelineAsset EnsureUrpAsset(UniversalRendererData rd)
        {
            var urp = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(kUrpPath);
            if (urp != null)
            {
                Debug.Log("[ProjectAuthor] URP asset exists: " + kUrpPath);
                return urp;
            }

            urp = UniversalRenderPipelineAsset.Create(rd);
            urp.name = "JSC-URP";
            AssetDatabase.CreateAsset(urp, kUrpPath);
            // Splats Z-test against the depth texture; keep it on.
            urp.supportsCameraDepthTexture = true;
            EditorUtility.SetDirty(urp);
            Debug.Log("[ProjectAuthor] created " + kUrpPath);
            return urp;
        }

        // ------------------------------------------------------------------ GraphicsSettings + URP global settings

        static void EnsureGraphicsSettings(UniversalRenderPipelineAsset urp)
        {
            RenderPipelineAsset current = GraphicsSettings.defaultRenderPipeline;
            if (current != urp)
            {
                GraphicsSettings.defaultRenderPipeline = urp;
                Debug.Log("[ProjectAuthor] GraphicsSettings.defaultRenderPipeline = " + kUrpPath);
            }
            else
            {
                Debug.Log("[ProjectAuthor] GraphicsSettings.defaultRenderPipeline already set");
            }

            // URP global settings (map + shader-variant collection): the class is editor-only and
            // internal to the URP editor assembly — reflection, best effort, non-fatal.
            try
            {
                Type gsType = Type.GetType(
                    "UnityEditor.Rendering.Universal.UniversalRenderPipelineGlobalSettings, Unity.RenderPipelines.Universal.Editor");
                if (gsType == null)
                {
                    Debug.LogWarning("[ProjectAuthor] URP global-settings editor type not found; map injection skipped.");
                    return;
                }
                MethodInfo ensure = gsType.GetMethod("Ensure", BindingFlags.Public | BindingFlags.Static);
                object gs = ensure != null ? ensure.Invoke(null, null) : null;
                if (gs == null)
                {
                    Debug.LogWarning("[ProjectAuthor] UniversalRenderPipelineGlobalSettings.Ensure() returned null; map injection skipped.");
                    return;
                }
                MethodInfo register = typeof(GraphicsSettings).GetMethod(
                    "RegisterRenderPipelineSettings", BindingFlags.Public | BindingFlags.Static);
                if (register != null)
                {
                    register.MakeGenericMethod(gs.GetType()).Invoke(null, new object[] { gs });
                    Debug.Log("[ProjectAuthor] URP global settings registered (" + gs.GetType().Name + ")");
                }
                else
                {
                    Debug.LogWarning("[ProjectAuthor] GraphicsSettings.RegisterRenderPipelineSettings missing; map injection skipped.");
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("[ProjectAuthor] URP global-settings step failed (continuing): " + e.Message);
            }
        }

        // ------------------------------------------------------------------ fog volume (component resolved by name)

        static VolumeProfile EnsureFogProfile()
        {
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(kFogProfilePath);
            if (profile != null) return profile;

            profile = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(profile, kFogProfilePath);

            Type fogType = FindFogType();
            if (fogType == null)
            {
                Debug.LogWarning("[ProjectAuthor] Fog override type not found; profile created without fog.");
                return profile;
            }
            MethodInfo add = typeof(VolumeProfile).GetMethod("Add", new[] { typeof(bool) });
            MethodInfo addGeneric = add != null ? add.MakeGenericMethod(fogType) : null;
            if (addGeneric == null)
            {
                Debug.LogWarning("[ProjectAuthor] VolumeProfile.Add<T> not found; fog not added.");
                return profile;
            }
            var fog = addGeneric.Invoke(profile, new object[] { true }) as VolumeComponent;
            if (fog != null)
            {
                SetVolumeParam(fog, "mode", (int)FogMode.Exponential);
                SetVolumeParam(fog, "density", 0.03f);
                SetVolumeParam(fog, "color", new Color(0.08f, 0.09f, 0.12f));
                EditorUtility.SetDirty(profile);
                Debug.Log("[ProjectAuthor] fog override added to " + kFogProfilePath);
            }
            return profile;
        }

        static Type FindFogType()
        {
            string[] candidates =
            {
                "UnityEngine.Rendering.Fog, Unity.RenderPipelines.Core.Runtime",
                "UnityEngine.Rendering.Fog, Unity.RenderPipelines.Universal.Runtime",
                "UnityEngine.Rendering.Universal.Fog, Unity.RenderPipelines.Universal.Runtime",
            };
            foreach (string candidate in candidates)
            {
                Type t = Type.GetType(candidate);
                if (t != null) return t;
            }
            return null;
        }

        static void SetVolumeParam(VolumeComponent component, string name, object value)
        {
            foreach (VolumeParameter p in component.parameters)
            {
                if (p.parameterName != name) continue;
                p.overrideState = true;
                try
                {
                    p.value = value;
                }
                catch (Exception e)
                {
                    Debug.LogWarning("[ProjectAuthor] SetVolumeParam '" + name + "' failed: " + e.Message);
                }
                return;
            }
            Debug.Log("[ProjectAuthor] volume param '" + name + "' not found on " +
                      component.GetType().Name + "; skipped (non-fatal).");
        }

        // ------------------------------------------------------------------ scene

        static void EnsureScene(VolumeProfile fogProfile)
        {
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(kScenePath) != null)
            {
                Debug.Log("[ProjectAuthor] scene exists: " + kScenePath);
                return;
            }

            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            // BlockBuilder owns geometry AND the player rig — never author player objects here.
            GameObject builderGO = new GameObject("BlockBuilder");
            var builder = builderGO.AddComponent<BlockBuilder>();
            builder.buildOnAwake = true;
            builder.includeEvidenceGates = true;
            builder.arcadeLength = 72f;

            new GameObject("EvidenceDriver").AddComponent<EvidenceDriver>();

            // Top-level anchor: BlockBuilder.PlaceSplatAnchor finds it by name at build time.
            GameObject anchorGO = new GameObject("SplatAnchor");
            var splat = anchorGO.AddComponent<GaussianSplatRenderer>();
            splat.m_SourcePath = kSplatSource; // staged into Assets/StreamingAssets by Build.ps1
            splat.m_SplatScale = 1.0f;
            splat.m_OpacityScale = 1.0f;
            splat.m_SHOrder = 3;
            anchorGO.transform.position = new Vector3(0f, 1.1f, 76f); // re-placed by Build() anyway

            GameObject volumeGO = new GameObject("Global Volume (Fog)");
            var volume = volumeGO.AddComponent<Volume>();
            volume.isGlobal = true;
            volume.priority = 0f;
            volume.sharedProfile = fogProfile;

            EditorSceneManager.MarkSceneDirty(scene);
            bool saved = EditorSceneManager.SaveScene(scene, kScenePath);
            if (!saved)
            {
                throw new InvalidOperationException("[ProjectAuthor] failed to save " + kScenePath);
            }
            Debug.Log("[ProjectAuthor] created + saved " + kScenePath +
                      " (BlockBuilder owns geometry + PlayerRig/FpsController/Camera; " +
                      "EvidenceDriver; SplatAnchor -> " + kSplatSource + "; global fog volume)");

            EditorSceneManager.OpenScene(kScenePath, OpenSceneMode.Single);
        }

        // ------------------------------------------------------------------ build settings

        static void EnsureBuildSettings()
        {
            var scenes = new List<EditorBuildSettingsScene>(EditorBuildSettings.scenes);
            foreach (EditorBuildSettingsScene s in scenes)
            {
                if (s.path == kScenePath)
                {
                    Debug.Log("[ProjectAuthor] EditorBuildSettings already contains " + kScenePath);
                    return;
                }
            }
            scenes.Add(new EditorBuildSettingsScene(kScenePath, true));
            EditorBuildSettings.scenes = scenes.ToArray();
            Debug.Log("[ProjectAuthor] EditorBuildSettings.scenes += " + kScenePath);
        }
    }
}
