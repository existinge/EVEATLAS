// Japanese Splat City — runtime block builder (DRAFT, NOT YET COMPILED).
//
// Builds the entire enclosed walkable block from primitives at runtime so the
// scene file can stay minimal (BlockBuilder GO + EvidenceDriver GO + SplatAnchor
// GO) until the first editor import is possible on a licensed host.
//
// Layout (top-down, +X = street side / annex, +Z = arcade direction, Y up):
//   - Arcade: 4.0 m wide (x in [-2.1, +2.1]), length = arcadeLength (64 m
//     inside walls, within the required 60-90 m), ceiling 3.6 m.
//   - Storefront bays on both arcade faces (protruding 0.42 m into the arcade),
//     alternating shutter / lit-window variants, sign rails + sign panels above.
//   - Far end (z = arcadeLength): boundary wall with a glazed street viewport;
//     the Gaussian-splat street anchor ("SplatAnchor") is placed beyond it so
//     the URP Z-tested splat is the view straight ahead from the spawn.
//   - Service lane (annex, x in [2.28, 6.96]): 2.2 m wide ring corridor.
//     CONNECTION 1 near the start (partition door at z ~= 8), CONNECTION 2 at
//     the rejoin (partition door at z ~= 40). Four 90-degree bends around an
//     inner core; exactly two connections to the arcade, no dead ends.
//   - Rejoin dressing at CONNECTION 2: striped awning, vending machines,
//     café windows (emissive + point lights, warm).
//   - Canopy over the arcade: alternating translucent canopy segments and sky
//     gaps with lighting poles.
//
// Waypoint evidence tags match FpsAndCapture: spawn / junction / servicebend /
// rejoin (see docs/WALK_DESIGN.md). See WaypointGate + EvidenceDriver.
using UnityEngine;

namespace JapaneseSplatCity.Block
{
    public class BlockBuilder : MonoBehaviour
    {
        [Header("Configuration")]
        [Range(60f, 90f)] public float arcadeLength = 72f;   // wall-to-wall arcade length
        public float arcadeWidth = 4f;                        // interior width
        public float wallThickness = 0.28f;
        public float floorThickness = 0.28f;
        public float ceilingHeight = 3.6f;
        public float wallHeight = 4.0f;

        [Tooltip("Protrusion of storefront bay bodies into the arcade (m).")]
        public float bayDepth = 0.42f;
        public float bayWidth = 3.6f;
        public float bayHeight = 2.62f;
        public float baySpacing = 4.0f;

        public bool buildOnAwake = true;
        public bool includeEvidenceGates = true;

        [Header("Runtime output")]
        public Transform playerSpawn;  // filled by Build()

        // Reusable palette (shared materials -> renderer batching friendly).
        Material _matConcrete;
        Material _matFloor;
        Material _matDark;
        Material _matWhite;
        Material _matWarm;
        Material _matEmissiveWarm;
        Material _matEmissiveCool;
        Material _matSign;
        Material _matCanopy;
        Material _matGlass;
        Material _matAwningRed;
        Material _matAwningWhite;

        // Signage generated offline by native/Tools/rasterize-jp-text.ps1 from the
        // licensed Noto Sans CJK JP (OFL) and verified by verify-font-glyphs.ps1.
        // PNGs live under Assets/Resources/Textures/Signs so Resources.Load works
        // with zero editor work on first import. Fallback = flat _matSign color.
        static readonly string[] SignSlates = {
            "ramen", "izakaya", "kissaten", "kissaten2", "konbini", "wagashi",
            "yakitori", "kanmi", "oden", "zakka", "yofuku", "hana", "hon",
            "kambutsu", "seiniku", "kusuri", "sento", "koban", "iriguchi", "deguchi"
        };
        int _bayCounter;

        // Arcade geometry anchors.
        const float ArcadeX = 2.1f;     // interior half-width
        const float AnnexX0 = 2.28f;   // lane inner edge (annex side of partition)
        const float AnnexX1 = 6.96f;   // lane outer edge
        const float LaneX0 = 4.48f;    // divider between lane legs
        const float LaneX1 = 4.76f;
        const float Door1Z0 = 7.4f;    // CONNECTION 1 gap (partition)
        const float Door1Z1 = 8.6f;
        const float Door2Z0 = 39.4f;   // CONNECTION 2 gap (partition)
        const float Door2Z1 = 40.6f;

        public void Awake()
        {
            if (buildOnAwake) Build();
        }

        public void Build()
        {
            float L = arcadeLength;
            float hw = wallHeight;      // outer wall top
            float ch = ceilingHeight;   // walkable ceiling
            Transform root = new GameObject("Block").transform;

            BuildMaterials();

            // ---- Full footprint floor slab ---------------------------------
            float floorW = ArcadeX * 2f + wallThickness * 2f + (AnnexX1 - ArcadeX) + wallThickness;
            float floorLen = L + wallThickness * 2f;
            float floorX = -(floorW - (AnnexX1 - ArcadeX) - wallThickness) / 2f; // keep arcade centered
            Box("Floor", root, new Vector3(floorX, 0.14f, floorLen / 2f - 0.14f),
                new Vector3(floorW, floorThickness, floorLen), _matFloor,
                collider: true, yCenter: 0.14f);

            // ---- Arcade side walls + near-end boundary wall ------------------
            // near end (z = 0): full wall
            BoxWall(root, new Vector3(0f, hw / 2f, -wallThickness / 2f),
                new Vector3(ArcadeX * 2f + wallThickness, hw, wallThickness));
            // side walls (x = +/- (arcadeX + wallThickness/2))
            BoxWall(root, new Vector3(ArcadeX + wallThickness / 2f, hw / 2f, L / 2f),
                new Vector3(wallThickness, hw, L + wallThickness));
            BoxWall(root, new Vector3(-(ArcadeX + wallThickness / 2f), hw / 2f, L / 2f),
                new Vector3(wallThickness, hw, L + wallThickness));

            // ---- Far end wall with glazed street viewport --------------------
            float paneHalf = 1.6f;      // pane half-width
            float paneBot = 0.65f, paneTop = 3.35f;
            float zEnd = L + wallThickness / 2f;
            // bottom, top, left, right wall segments around the pane
            BoxWall(root, new Vector3(0f, paneBot / 2f, zEnd),
                new Vector3(ArcadeX * 2f + wallThickness, paneBot, wallThickness));
            BoxWall(root, new Vector3(0f, (hw + paneTop) / 2f, zEnd),
                new Vector3(ArcadeX * 2f + wallThickness, hw - paneTop, wallThickness));
            BoxWall(root, new Vector3(-(ArcadeX + wallThickness / 2f) + (ArcadeX - paneHalf) / 2f, (paneBot + paneTop) / 2f, zEnd),
                new Vector3(ArcadeX - paneHalf + wallThickness, paneTop - paneBot, wallThickness));
            BoxWall(root, new Vector3((ArcadeX + wallThickness / 2f) - (ArcadeX - paneHalf) / 2f, (paneBot + paneTop) / 2f, zEnd),
                new Vector3(ArcadeX - paneHalf + wallThickness, paneTop - paneBot, wallThickness));
            // glazing itself (no collider -> splat visible through it)
            Box("Glazing", root, new Vector3(0f, (paneBot + paneTop) / 2f, L - 0.04f),
                new Vector3(paneHalf * 2f, paneTop - paneBot, 0.06f), _matGlass, collider: false);

            // ---- Partition wall (arcade | lane) with two connections ---------
            BuildPartition(root, L);

            // ---- Annex solid fill around the lane corridor --------------------
            // (builds the ring voids by solid fill; see class header diagram)
            // north fill (above CONNECTION 1)
            BoxSolidFill(root, new Vector3((AnnexX0 + (AnnexX1 + wallThickness)) / 2f, hw / 2f, (Door1Z0 + 0f) / 2f),
                new Vector3((AnnexX1 + wallThickness) - AnnexX0, hw, Door1Z0));
            // south fill (below CONNECTION 2)
            BoxSolidFill(root, new Vector3((AnnexX0 + (AnnexX1 + wallThickness)) / 2f, hw / 2f, (L + Door2Z1) / 2f),
                new Vector3((AnnexX1 + wallThickness) - AnnexX0, hw, L - Door2Z1));
            // east boundary wall of annex
            BoxWall(root, new Vector3(AnnexX1 + wallThickness / 2f, hw / 2f, L / 2f),
                new Vector3(wallThickness, hw, L + wallThickness));
            // straight-line block (west portion between leg 1 and the rejoin pocket)
            BoxSolidFill(root, new Vector3(4.62f, hw / 2f, 36.9f),
                new Vector3(2.34f, hw, 8.6f));
            // divider between lane legs (x = LaneX0..LaneX1, z = 8..32.2)
            BoxWall(root, new Vector3((LaneX0 + LaneX1) / 2f, hw / 2f, (8f + 32.2f) / 2f),
                new Vector3(LaneX1 - LaneX0, hw, 32.2f - 8f));
            // vertical core west of the divider (forces the corridor to bend east,
            // and blocks any straight-line shortcut back to CONNECTION 1)
            BoxSolidFill(root, new Vector3(4.62f, hw / 2f, 20.1f),
                new Vector3(2.2f, hw, 24.2f));
            // core above the return pocket forcing the U-turn chamber shape;
            // final positions are editor-tuned once the loop is playable
            BoxSolidFill(root, new Vector3(5.0f, hw / 2f, 29.0f),
                new Vector3(1.6f, hw, 8.0f));

            // ---- Lane corridor ceiling + floor patches (visually) -------------
            // one slab over the whole lane zone; ceiling only (floor already covered)
            Box("LaneCeiling", root, new Vector3((AnnexX0 + AnnexX1) / 2f, ch + 0.1f, (Door1Z0 + Door2Z1) / 2f),
                new Vector3(AnnexX1 - AnnexX0, 0.2f, Door2Z1 - Door1Z0), _matConcrete, collider: false);

            // ---- Arcade canopy: alternating translucent / open gaps -----------
            BuildCanopy(root, L);

            // ---- Storefront bays on both arcade faces --------------------------
            BuildBays(root, L);

            // ---- Block signage ---------------------------------------------------
            // Arcade title banner 商店街 on the far wall above the glazed viewport
            // (reads as the block head; the splat sits at z = L + 4 behind the glass).
            GameObject titlePanel = Box("SignArcadeTitle", root,
                new Vector3(0f, (wallHeight + 3.35f) / 2f - 0.05f, zEnd - wallThickness / 2f - 0.04f),
                new Vector3(5.6f, 0.55f, 0.06f), _matSign, collider: false);
            ApplySignTexture(titlePanel, "arcade-title");
            // 入口 / 出口 guidance flaps on the partition, arcade side of both doors
            GameObject inPanel = Box("SignIriguchi", root,
                new Vector3(ArcadeX - 0.15f, 1.9f, Door1Z0 - 0.8f),
                new Vector3(0.06f, 0.32f, 0.5f), _matSign, collider: false);
            ApplySignTexture(inPanel, "iriguchi");
            GameObject outPanel = Box("SignDeguchi", root,
                new Vector3(ArcadeX - 0.15f, 1.9f, Door2Z1 + 0.8f),
                new Vector3(0.06f, 0.32f, 0.5f), _matSign, collider: false);
            ApplySignTexture(outPanel, "deguchi");

            // ---- Rejoin dressing: awning, vending nook, café windows -----------
            BuildRejoin(root);

            // ---- Lighting ------------------------------------------------------
            BuildLights(root, L);

            // ---- Player rig -----------------------------------------------------
            BuildPlayer(root, L);

            // ---- Splat anchor --------------------------------------------------
            PlaceSplatAnchor(root, L);

            // ---- Evidence gates -------------------------------------------------
            if (includeEvidenceGates) BuildGates(root, L);

            Debug.Log("[BlockBuilder] block built: arcade " + (L - 4f) + "m walkable, lane ring with 2 connections");
        }

        // ---------------------------------------------------------------------
        // Construction helpers
        // ---------------------------------------------------------------------

        void BuildMaterials()
        {
            _matConcrete = Mat("concrete", new Color(0.45f, 0.46f, 0.47f), 0.9f);
            _matFloor = Mat("floor", new Color(0.30f, 0.27f, 0.24f), 0.9f);
            _matDark = Mat("dark", new Color(0.08f, 0.08f, 0.09f), 0.9f);
            _matWhite = Mat("white", new Color(0.88f, 0.86f, 0.82f), 0.95f);
            _matWarm = Mat("warm", new Color(0.95f, 0.72f, 0.5f), 0.95f);
            _matEmissiveWarm = Mat("emissive-warm", new Color(1.0f, 0.76f, 0.45f), 1.0f, emissive: new Color(2.2f, 1.35f, 0.7f) * 2f);
            _matEmissiveCool = Mat("emissive-cool", new Color(0.7f, 0.9f, 1.0f), 1.0f, emissive: new Color(0.5f, 0.9f, 1.3f) * 2f);
            _matSign = Mat("sign", new Color(0.12f, 0.30f, 0.45f), 0.9f);
            _matCanopy = Mat("canopy", new Color(0.85f, 0.55f, 0.35f), 0.9f, alpha: 0.55f);
            _matGlass = Mat("glass", new Color(0.75f, 0.88f, 0.95f), 1.0f, alpha: 0.24f);
            _matAwningRed = Mat("awning-red", new Color(0.78f, 0.16f, 0.14f), 0.9f);
            _matAwningWhite = Mat("awning-white", new Color(0.93f, 0.92f, 0.88f), 0.9f);
        }

        // Shared material with URP Lit primary + Standard/Unlit fallbacks.
        static Material Mat(string name, Color baseColor, float smoothness, Color? emissive = null, float alpha = 1f)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) shader = Shader.Find("Standard");
            if (shader == null) shader = Shader.Find("Unlit/Color");

            var m = new Material(shader);
            m.name = "mat-" + name;
            if (alpha < 1f)
            {
                shader = Shader.Find("Legacy Shaders/Transparent/Diffuse");
                if (shader != null) m.shader = shader;
            }
            Color c = baseColor;
            c.a = alpha;
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
            if (m.HasProperty("_Color")) m.SetColor("_Color", c);
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", smoothness);
            if (alpha < 1f && m.HasProperty("_Mode")) m.SetFloat("_Mode", 3f);
            if (emissive.HasValue)
            {
                if (m.HasProperty("_EmissionColor"))
                {
                    m.EnableKeyword("_EMISSION");
                    m.SetColor("_EmissionColor", emissive.Value);
                }
            }
            return m;
        }

        GameObject Box(string name, Transform parent, Vector3 center, Vector3 size,
            Material mat, bool collider = true, float yCenter = -1f)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.position = center;
            go.transform.localScale = size;
            var mr = go.GetComponent<MeshRenderer>();
            if (mr != null) mr.sharedMaterial = mat;
            if (!collider)
            {
                var col = go.GetComponent<Collider>();
                if (col != null) Destroy(col);
            }
            if (yCenter > 0f) go.transform.position = new Vector3(center.x, yCenter, center.z);
            go.isStatic = true;
            return go;
        }

        // Wall box from the floor top (floorThickness) up to wallHeight.
        void BoxWall(Transform root, Vector3 center, Vector3 size)
        {
            Box("Wall", root, center, size, _matConcrete);
        }

        // Solid mass filling regions that must not be walkable (spans floor->wall top).
        void BoxSolidFill(Transform root, Vector3 center, Vector3 size)
        {
            Box("Fill", root, center, size, _matConcrete);
        }

        void BuildPartition(Transform root, float L)
        {
            float px = ArcadeX + wallThickness / 2f; // x center of partition
            // three segments around the two door gaps
            BoxWall(root, new Vector3(px, 4f / 2f, (0f + Door1Z0) / 2f),
                new Vector3(wallThickness, 4f, Door1Z0));
            BoxWall(root, new Vector3(px, 4f / 2f, (Door1Z1 + Door2Z0) / 2f),
                new Vector3(wallThickness, 4f, Door2Z0 - Door1Z1));
            BoxWall(root, new Vector3(px, 4f / 2f, (Door2Z1 + L) / 2f),
                new Vector3(wallThickness, 4f, L - Door2Z1));
            // door lintels (visual only, above head height)
            Box("DoorLintel1", root, new Vector3(px, 4f - 0.14f, (Door1Z0 + Door1Z1) / 2f),
                new Vector3(wallThickness, 0.28f, Door1Z1 - Door1Z0), _matConcrete, collider: false);
            Box("DoorLintel2", root, new Vector3(px, 4f - 0.14f, (Door2Z0 + Door2Z1) / 2f),
                new Vector3(wallThickness, 0.28f, Door2Z1 - Door2Z0), _matConcrete, collider: false);
        }

        void BuildCanopy(Transform root, float L)
        {
            float cover = 4f;   // covered length per segment
            float gap = 2f;     // open gap with lighting pole
            float seg = cover + gap;
            int n = Mathf.FloorToInt((L - 6f) / seg);
            for (int i = 0; i < n; i++)
            {
                float z0 = 3f + i * seg;
                // translucent canopy slab over the arcade interior
                Box("Canopy", root, new Vector3(0f, 3.62f, z0 + cover / 2f),
                    new Vector3(ArcadeX * 2f, 0.12f, cover), _matCanopy, collider: false);
                // lighting pole in the gap
                float pz = z0 + cover + gap / 2f;
                var pole = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                pole.name = "LightPole";
                pole.transform.SetParent(root, false);
                pole.transform.position = new Vector3(0f, 2.6f, pz);
                pole.transform.localScale = new Vector3(0.07f, 2.6f, 0.07f);
                Destroy(pole.GetComponent<Collider>());
                pole.GetComponent<MeshRenderer>().sharedMaterial = _matDark;
                var lightBar = Box("PoleLight", root, new Vector3(0f, 3.95f, pz),
                    new Vector3(0.34f, 0.10f, 1.6f), _matEmissiveWarm, collider: false);
                Light l = lightBar.AddComponent<Light>();
                l.type = LightType.Point;
                l.color = new Color(1f, 0.85f, 0.65f);
                l.range = 7f;
                l.intensity = 1.1f;
                l.shadows = LightShadows.Soft;
            }
        }

        // Bays: variant 0 = shutter down, 1 = lit window; deterministic pattern.
        void BuildBays(Transform root, float L)
        {
            float startZ = 6f;
            float endZ = L - 6f;
            float pw = ArcadeX + wallThickness / 2f + bayDepth / 2f; // bay center protrusion
            int count = Mathf.FloorToInt((endZ - startZ) / baySpacing);
            int seedBase = 7;
            for (int i = 0; i < count; i++)
            {
                float zCenter = startZ + i * baySpacing + baySpacing / 2f;
                // skip bays where the rejoin dressing lives (arcade side of CONNECTION 2)
                if (zCenter > Door2Z0 - 1.4f && zCenter < Door2Z1 + 1.4f) continue;
                bool lit = ((seedBase + i * 3) % 3) != 0; // ~2/3 lit
                foreach (int side in new int[] { -1, 1 })
                {
                    BuildBay(root, side * pw, zCenter, side, lit, (zCenter * 100f + side * 50f) % 13f);
                }
            }
        }

        void BuildBay(Transform root, float xCenter, float zCenter, int side, bool lit, float seed)
        {
            // recessed storefront body (protrudes bayDepth into the arcade)
            Box("Bay", root, new Vector3(xCenter, 1.31f + 0.28f / 2f, zCenter),
                new Vector3(bayDepth + wallThickness, bayHeight, bayWidth), _matConcrete);

            float faceX = xCenter - side * (bayDepth / 2f + wallThickness / 2f);

            if (lit)
            {
                // lit window: emissive pane + warm interior light
                Box("BayWindow", root, new Vector3(faceX, 1.85f, zCenter),
                    new Vector3(0.05f, 0.9f, 2.2f), _matEmissiveWarm, collider: false);
                // door frame (dark)
                Box("BayDoorFrame", root, new Vector3(faceX - side * 0.02f, 1.05f, zCenter - 1.35f),
                    new Vector3(0.06f, 1.9f, 0.9f), _matDark, collider: false);
                var go = Box("BayLight", root, new Vector3(faceX - side * 0.5f, 2.1f, zCenter), Vector3.one * 0.01f,
                    _matEmissiveWarm, collider: false);
                Light l = go.AddComponent<Light>();
                l.type = LightType.Point;
                l.color = new Color(1f, 0.8f, 0.6f);
                l.range = 3.4f;
                l.intensity = 1.0f;
                l.shadows = LightShadows.Soft;
            }
            else
            {
                // metal shutter: three horizontal slats + fascia
                for (int k = 0; k < 3; k++)
                {
                    Box("ShutterSlat", root, new Vector3(faceX, 1.05f + k * 0.62f, zCenter),
                        new Vector3(0.06f, 0.14f, bayWidth - 0.3f), _matDark, collider: false);
                }
                Box("Shutter", root, new Vector3(faceX, 2.0f, zCenter),
                    new Vector3(0.05f, 0.85f, bayWidth - 0.2f), _matDark, collider: false);
            }

            // sign rail + sign panel above the bay
            Box("SignRail", root, new Vector3(xCenter + side * (bayDepth + wallThickness) * 0.0f, 3.30f, zCenter),
                new Vector3(bayDepth + wallThickness + 0.1f, 0.10f, bayWidth + 0.3f), _matDark, collider: false);
            GameObject panel = Box("SignPanel", root, new Vector3(xCenter + side * 0.05f, 3.56f, zCenter),
                new Vector3(bayDepth + wallThickness + 0.12f, 0.42f, bayWidth + 0.2f), _matSign, collider: false);
            ApplySignTexture(panel, SignSlates[_bayCounter++ % SignSlates.Length]);
        }

        // Swaps the flat sign material for the generated signage texture, keeping
        // the texture's aspect ratio by cropping (never squashing) it to the panel.
        void ApplySignTexture(GameObject panel, string signTag)
        {
            var tex = Resources.Load<Texture2D>("Textures/Signs/sign-" + signTag);
            if (tex == null) return; // flat-color fallback (e.g. no imported assets yet)
            var r = panel.GetComponent<Renderer>();
            if (r == null) return;
            var m = new Material(_matSign);
            m.mainTexture = tex;
            Vector3 s = panel.transform.localScale;
            float texAspect = tex.width / (float)tex.height;
            float panelAspect = s.z / s.y;
            if (texAspect >= panelAspect)
            {
                float sx = texAspect / panelAspect;
                m.mainTextureScale = new Vector2(sx, 1f);
                m.mainTextureOffset = new Vector2(-(sx - 1f) / 2f, 0f);
            }
            else
            {
                float sy = panelAspect / texAspect;
                m.mainTextureScale = new Vector2(1f, sy);
                m.mainTextureOffset = new Vector2(0f, -(sy - 1f) / 2f);
            }
            r.sharedMaterial = m;
        }

        // Rejoin dressing at CONNECTION 2 (arcade side of the partition, z ~= 40):
        // striped awning over the doorway, vending machines, café windows.
        void BuildRejoin(Transform root)
        {
            float px = ArcadeX + wallThickness / 2f;
            // striped awning: six slats fanning out over the door
            for (int k = 0; k < 6; k++)
            {
                float zOff = Door2Z0 - 0.1f - k * 0.30f;
                var slat = Box("AwningSlat", root, new Vector3(px + 0.02f, 2.95f - k * 0.055f, zOff),
                    new Vector3(2.2f, 0.035f, 0.42f), (k % 2 == 0) ? _matAwningRed : _matAwningWhite,
                    collider: false);
                slat.transform.localRotation = Quaternion.Euler(-19f, 0f, 0f);
            }
            // vending machines in a nook beside the door
            float[] vz = { Door2Z1 + 1.1f, Door2Z1 + 2.2f };
            for (int k = 0; k < vz.Length; k++)
            {
                var v = Box("Vending", root, new Vector3(px - 0.06f, 1.20f, vz[k]),
                    new Vector3(0.42f, 2.0f, 0.72f), _matEmissiveCool, collider: false);
                Box("VendingFace", root, new Vector3(px - 0.26f, 1.20f, vz[k]),
                    new Vector3(0.04f, 1.7f, 0.6f), _matEmissiveCool, collider: false);
            }
            Light vl = Box("VendingLight", root, new Vector3(px - 0.5f, 2.4f, Door2Z1 + 1.65f),
                Vector3.one * 0.01f, _matEmissiveCool, collider: false).AddComponent<Light>();
            vl.type = LightType.Point;
            vl.color = new Color(0.65f, 0.9f, 1f);
            vl.range = 3.0f;
            vl.intensity = 0.9f;
            vl.shadows = LightShadows.None;

            // café windows flanking the doorway (warm)
            float[] wz = { (Door2Z0 - 1.55f), (Door2Z1 + 1.55f) };
            for (int k = 0; k < wz.Length; k++)
            {
                Box("CafeWindow", root, new Vector3(px - 0.02f, 1.7f, wz[k]),
                    new Vector3(0.06f, 1.2f, 1.5f), _matEmissiveWarm, collider: false);
                Light cl = Box("CafeLight", root, new Vector3(px - 0.4f, 2.2f, wz[k]),
                    Vector3.one * 0.01f, _matEmissiveWarm, collider: false).AddComponent<Light>();
                cl.type = LightType.Point;
                cl.color = new Color(1f, 0.82f, 0.6f);
                cl.range = 2.8f;
                cl.intensity = 0.9f;
                cl.shadows = LightShadows.None;
            }
        }

        void BuildLights(Transform root, float L)
        {
            // ambient dusk scene (street lights do the talking)
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.25f, 0.26f, 0.3f);
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.08f, 0.09f, 0.12f);
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogStartDistance = 30f;
            RenderSettings.fogEndDistance = 80f;

            // key light: dusk directional
            var dgo = new GameObject("Sun");
            dgo.transform.SetParent(root, false);
            dgo.transform.rotation = Quaternion.Euler(45f, -35f, 0f);
            var sun = dgo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.color = new Color(1f, 0.85f, 0.68f);
            sun.intensity = 1.1f;
            sun.shadows = LightShadows.Soft;
        }

        void BuildPlayer(Transform root, float L)
        {
            var rig = new GameObject("PlayerRig");
            rig.transform.SetParent(root, false);
            rig.transform.position = new Vector3(-0.8f, 0f, 2.5f);
            rig.transform.rotation = Quaternion.Euler(0f, -6f, 0f); // faces first lit bay, slightly right

            var cc = rig.AddComponent<CharacterController>();
            cc.height = 1.8f;
            cc.radius = 0.35f;
            cc.center = new Vector3(0f, 0.9f, 0f);

            var fps = rig.AddComponent<Player.FpsController>();
            fps.walkSpeed = 4f;

            var camGo = new GameObject("PlayerCamera");
            camGo.transform.SetParent(rig.transform, false);
            camGo.transform.localPosition = new Vector3(0f, 1.62f, 0f);
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.fieldOfView = 70f;
            cam.nearClipPlane = 0.08f;
            cam.farClipPlane = 300f;
            camGo.AddComponent<AudioListener>();
            fps.cam = camGo.transform;
            playerSpawn = rig.transform;

            // capsule collider-shaped visual: primitive capsule disabled? use a
            // low alpha marker instead; the controller is invisible by design
        }

        void PlaceSplatAnchor(Transform root, float L)
        {
            var found = GameObject.Find("SplatAnchor");
            if (found == null)
            {
                Debug.LogWarning("[BlockBuilder] no top-level 'SplatAnchor' object found; " +
                                 "attach the GaussianSplatRenderer later (anchor at z=" + (L + 4f) + ").");
                return;
            }
            found.transform.position = new Vector3(0f, 1.1f, L + 4f);
            Debug.Log("[BlockBuilder] SplatAnchor placed at " + found.transform.position);
        }

        void BuildGates(Transform root, float L)
        {
            // junction: just inside CONNECTION 1 (arcade side)
            Gate(root, "junction", new Vector3(1.15f, 1f, Door1Z0 + 0.3f), new Vector3(2.0f, 2.2f, 1.4f));
            // servicebend: inside the lane ring, first corner
            Gate(root, "servicebend", new Vector3(4.2f, 1f, 31.1f), new Vector3(1.5f, 2.2f, 1.6f));
            // rejoin: just past CONNECTION 2 (arcade side)
            Gate(root, "rejoin", new Vector3(1.15f, 1f, Door2Z1 + 0.25f), new Vector3(2.0f, 2.2f, 1.4f));
        }

        void Gate(Transform root, string tag, Vector3 center, Vector3 size)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = "Gate-" + tag;
            go.transform.SetParent(root, false);
            go.transform.position = center;
            go.transform.localScale = size;
            Destroy(go.GetComponent<MeshRenderer>());
            Destroy(go.GetComponent<MeshCollider>());
            var bc = go.AddComponent<BoxCollider>();
            bc.isTrigger = true;
            bc.size = Vector3.one;
            bc.center = Vector3.zero;
            go.AddComponent<WaypointGate>().tagName = tag;
        }
    }
}
