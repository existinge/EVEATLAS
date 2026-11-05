/**
 * Milestone M4 — the interactable defs of the street.
 *
 * 12 interactables: 8 shopfronts (one per building in BUILDING_BASES), the
 * street monument and the 3 M3 street props. Shop hotspots are thin trigger
 * slabs flush with each building facade, derived here from BUILDING_BASES so
 * they can never drift from the visible/collidable world; prop and monument
 * hotspots are small boxes placed clear of every collision solid (road,
 * buildings, lamp poles, monument footprint) — `tests/interaction.test.ts`
 * verifies all of that.
 *
 * The `label` / `reading` / `description` / `message` fields are the shared
 * interaction+data hook with milestone M5 (vocabulary learning): M5 consumes
 * these exact entries, it does not introduce a second registry.
 */

import type { Aabb3, InteractiveDef } from '../interaction/Interaction';
import {
  BUILDING_BASES,
  MONUMENT,
  STREET_PROPS,
  monumentFootprint,
} from './ShoppingStreet';

/** Max reach distance (meters) for targeting and pressing E. */
export const INTERACTION_DISTANCE = 4.6;

/** Trigger-slab thickness in front of each shop facade (meters). */
const SHOP_SLAB_DEPTH = 0.2;
/** Half-width of the hotspot band across each shopfront (meters). */
const SHOP_SLAB_SPAN = 1.0;
/** Shop hotspot height band (ground to above the signboard). */
const SHOP_Y = { minY: 0, maxY: 3.2 };

/** Hotspot half-extent around each street prop's ground point. */
const PROP_HALF = 0.25;

/**
 * One entry per BUILDING_BASES record (order matches), mapping the toy shop
 * to a Japanese shop type; the slabs themselves are computed below.
 */
const SHOP_TYPES: ReadonlyArray<{
  id: string;
  label: string;
  reading: string;
  description: string;
  message: string;
  action: string;
}> = [
  {
    id: 'shop-ramen-ya',
    label: 'ラーメン屋',
    reading: 'ラーメンや',
    description: 'あついラーメンを売っているおみせです。',
    message: 'のれんをくぐって、ラーメンを注文しました。',
    action: '注文する',
  },
  {
    id: 'shop-hon-ya',
    label: '本屋',
    reading: 'ほんや',
    description: 'ほんとざっしがたくさんあります。',
    message: '本棚をながめて、まんがをえらびました。',
    action: '見る',
  },
  {
    id: 'shop-wagashi',
    label: '和菓子店',
    reading: 'わがしてん',
    description: 'だんごやまんじゅうがならんでいます。',
    message: 'おまんじゅうをひとつ買いました。',
    action: '買う',
  },
  {
    id: 'shop-kissaten',
    label: '喫茶店',
    reading: 'きっさてん',
    description: 'コーヒーとケーキのおみせです。',
    message: 'ブレンドコーヒーを注文しました。',
    action: '注文する',
  },
  {
    id: 'shop-konbini',
    label: 'コンビニ',
    reading: 'コンビニ',
    description: 'よるおそくまで開いています。',
    message: 'おにぎりとおちゃを買いました。',
    action: '買う',
  },
  {
    id: 'shop-hana-ya',
    label: '花屋',
    reading: 'はなや',
    description: 'きれいな花がたくさんあります。',
    message: 'ひまわりを一本買いました。',
    action: '買う',
  },
  {
    id: 'shop-zakka-ten',
    label: '雑貨店',
    reading: 'ざっかてん',
    description: 'ふうりんやてぬぐいが売っています。',
    message: 'おみやげのてぬぐいを選びました。',
    action: '選ぶ',
  },
  {
    id: 'shop-sento',
    label: '銭湯',
    reading: 'せんとう',
    description: 'おゆでからだをあたためるおふろです。',
    message: 'のれんをくぐって、おふろに入りました。',
    action: '入る',
  },
];

function shopSlab(building: (typeof BUILDING_BASES)[number]): Aabb3 {
  const sign = building.x > 0 ? 1 : -1;
  const face = building.x - (sign * building.w) / 2;
  const near = face - sign * SHOP_SLAB_DEPTH;
  return {
    minX: Math.min(face, near),
    maxX: Math.max(face, near),
    minZ: building.z - SHOP_SLAB_SPAN,
    maxZ: building.z + SHOP_SLAB_SPAN,
    ...SHOP_Y,
  };
}

function propBox(
  name: string,
  at: { x: number; z: number },
  label: string,
  reading: string,
  description: string,
  message: string,
  action: string,
): InteractiveDef {
  return {
    id: `prop-${name}`,
    label,
    reading,
    description,
    message,
    action,
    box: {
      minX: at.x - PROP_HALF,
      maxX: at.x + PROP_HALF,
      minY: 0,
      maxY: 2.2,
      minZ: at.z - PROP_HALF,
      maxZ: at.z + PROP_HALF,
    },
  };
}

function buildInteractables(): readonly InteractiveDef[] {
  const defs: InteractiveDef[] = [];
  for (let i = 0; i < BUILDING_BASES.length; i++) {
    const type = SHOP_TYPES[i];
    const building = BUILDING_BASES[i];
    defs.push({
      id: type.id,
      label: type.label,
      reading: type.reading,
      description: type.description,
      message: type.message,
      action: type.action,
      box: shopSlab(building),
    });
  }

  // Street monument: a box in front of (north of) the plinth — the spot the
  // player stands on to admire the carved head. x matches the footprint width.
  const footprint = monumentFootprint(MONUMENT.scale);
  defs.push({
    id: 'monument',
    label: '牛の石像',
    reading: 'うしのせきぞう',
    description: 'まちのシンボルです。おまつりのときは花をそなえます。',
    message: '石の牛をじっくり見ました。',
    action: '見る',
    box: {
      minX: footprint.minX,
      maxX: footprint.maxX,
      minY: 0,
      maxY: 4.5,
      minZ: footprint.maxZ + 0.07,
      maxZ: footprint.maxZ + 1.6,
    },
  });

  // The three M3 street props, keyed by STREET_PROPS name.
  const propAt = (name: string) => {
    const def = STREET_PROPS.find((p) => p.name === name);
    if (!def) throw new Error(`M4: street prop "${name}" not found in STREET_PROPS`);
    return def.at;
  };
  defs.push(
    propBox(
      'apple',
      propAt('apple'),
      'りんご',
      'りんご',
      'あかいりんご、ひとつ。',
      'りんごを手に取りました。',
      '手に取る',
    ),
    propBox(
      'brass-diya-lantern',
      propAt('brass-diya-lantern'),
      'ランタン',
      'ランタン',
      'まちあかりのランタン。',
      'ランタンのあかりをながめました。',
      '見る',
    ),
    propBox(
      'concrete-cat-statue',
      propAt('concrete-cat-statue'),
      '猫の石像',
      'ねこのせきぞう',
      'おみせのまえにいる石のねこ。',
      '猫のあたまをなでました。',
      'なでる',
    ),
  );
  return defs;
}

/** All 12 interactables, in definition order (M4 → M5 data contract). */
export const INTERACTABLES: readonly InteractiveDef[] = buildInteractables();
