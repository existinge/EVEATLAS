/**
 * Milestone M5 — vocabulary content.
 *
 * Pure data, no DOM and no renderer imports, so the learning system and its
 * tests run in plain Node.
 *
 * The content is keyed to the M4 interaction registry: every entry names the
 * `interactableId` that teaches it, and every one of the 12 M4 interactables
 * teaches at least one word. There is no second registry — the M4
 * `INTERACTABLES` list stays the single source of truth for *where* a word is
 * found, and this file is the single source of truth for *what* is learned
 * there.
 *
 * Design constraint from the roadmap: N4–N3 words only, and **no
 * English→Japanese translation quizzes**. `meaning` and `exampleMeaning` are
 * reference glosses for the notebook; nothing in the schema is a quiz prompt,
 * a set of choices or an answer key.
 */

/** JLPT level of a word. M5 ships N4 and N3 content only. */
export type JlptLevel = 'N4' | 'N3';

/** Part of speech, used to group the notebook. */
export type PartOfSpeech = 'noun' | 'verb' | 'i-adj' | 'na-adj' | 'adverb' | 'expression';

export interface VocabularyEntry {
  /** Stable id, e.g. `v-chumon`. Never reused. */
  id: string;
  /** The word as written (kanji and/or kana). */
  word: string;
  /** Kana reading of {@link word}. */
  reading: string;
  /** Short English gloss — reference only, never a quiz prompt. */
  meaning: string;
  /** JLPT level. */
  level: JlptLevel;
  /** Part of speech. */
  pos: PartOfSpeech;
  /** Japanese example sentence that uses the word in this street's context. */
  example: string;
  /** English gloss of {@link example} — reference only. */
  exampleMeaning: string;
  /** The M4 interactable that teaches this word. */
  interactableId: string;
}

/** Levels in display order (easiest first). */
export const VOCABULARY_LEVELS: readonly JlptLevel[] = ['N4', 'N3'];

/**
 * The M5 word list: two words per M4 interactable, 24 in total
 * (17 × N4, 7 × N3).
 */
export const VOCABULARY: readonly VocabularyEntry[] = [
  // ----- ラーメン屋 -------------------------------------------------------
  {
    id: 'v-chumon',
    word: '注文',
    reading: 'ちゅうもん',
    meaning: 'order (a meal, goods)',
    level: 'N4',
    pos: 'noun',
    example: 'ラーメンを一つ注文しました。',
    exampleMeaning: 'I ordered one bowl of ramen.',
    interactableId: 'shop-ramen-ya',
  },
  {
    id: 'v-aji',
    word: '味',
    reading: 'あじ',
    meaning: 'taste, flavour',
    level: 'N4',
    pos: 'noun',
    example: 'このラーメンは味がこいです。',
    exampleMeaning: 'This ramen has a rich flavour.',
    interactableId: 'shop-ramen-ya',
  },

  // ----- 本屋 -------------------------------------------------------------
  {
    id: 'v-hondana',
    word: '本棚',
    reading: 'ほんだな',
    meaning: 'bookshelf',
    level: 'N4',
    pos: 'noun',
    example: '本棚にまんががならんでいます。',
    exampleMeaning: 'Manga are lined up on the bookshelf.',
    interactableId: 'shop-hon-ya',
  },
  {
    id: 'v-hyoushi',
    word: '表紙',
    reading: 'ひょうし',
    meaning: 'cover (of a book)',
    level: 'N3',
    pos: 'noun',
    example: '赤い表紙の本をえらびました。',
    exampleMeaning: 'I picked a book with a red cover.',
    interactableId: 'shop-hon-ya',
  },

  // ----- 和菓子店 ---------------------------------------------------------
  {
    id: 'v-amai',
    word: '甘い',
    reading: 'あまい',
    meaning: 'sweet',
    level: 'N4',
    pos: 'i-adj',
    example: 'このまんじゅうはとても甘いです。',
    exampleMeaning: 'This manjū is very sweet.',
    interactableId: 'shop-wagashi',
  },
  {
    id: 'v-kisetsu',
    word: '季節',
    reading: 'きせつ',
    meaning: 'season',
    level: 'N4',
    pos: 'noun',
    example: '季節の和菓子がならんでいます。',
    exampleMeaning: 'Seasonal sweets are on display.',
    interactableId: 'shop-wagashi',
  },

  // ----- 喫茶店 -----------------------------------------------------------
  {
    id: 'v-nigai',
    word: '苦い',
    reading: 'にがい',
    meaning: 'bitter',
    level: 'N4',
    pos: 'i-adj',
    example: 'ブラックコーヒーは苦いです。',
    exampleMeaning: 'Black coffee is bitter.',
    interactableId: 'shop-kissaten',
  },
  {
    id: 'v-shizuka',
    word: '静か',
    reading: 'しずか',
    meaning: 'quiet, calm',
    level: 'N4',
    pos: 'na-adj',
    example: 'この喫茶店は静かで、ゆっくりできます。',
    exampleMeaning: 'This coffee shop is quiet, so you can relax.',
    interactableId: 'shop-kissaten',
  },

  // ----- コンビニ ---------------------------------------------------------
  {
    id: 'v-benri',
    word: '便利',
    reading: 'べんり',
    meaning: 'convenient, handy',
    level: 'N4',
    pos: 'na-adj',
    example: 'コンビニはとても便利です。',
    exampleMeaning: 'Convenience stores are very convenient.',
    interactableId: 'shop-konbini',
  },
  {
    id: 'v-shinamono',
    word: '品物',
    reading: 'しなもの',
    meaning: 'goods, items',
    level: 'N3',
    pos: 'noun',
    example: '品物がたくさんならんでいます。',
    exampleMeaning: 'Lots of goods are on display.',
    interactableId: 'shop-konbini',
  },

  // ----- 花屋 -------------------------------------------------------------
  {
    id: 'v-hanabira',
    word: '花びら',
    reading: 'はなびら',
    meaning: 'petal',
    level: 'N3',
    pos: 'noun',
    example: '花びらが風にまっています。',
    exampleMeaning: 'Petals are dancing in the wind.',
    interactableId: 'shop-hana-ya',
  },
  {
    id: 'v-kaori',
    word: '香り',
    reading: 'かおり',
    meaning: 'scent, fragrance',
    level: 'N3',
    pos: 'noun',
    example: '花の香りがします。',
    exampleMeaning: 'There is a scent of flowers.',
    interactableId: 'shop-hana-ya',
  },

  // ----- 雑貨店 -----------------------------------------------------------
  {
    id: 'v-erabu',
    word: '選ぶ',
    reading: 'えらぶ',
    meaning: 'to choose, to pick',
    level: 'N4',
    pos: 'verb',
    example: 'おみやげを一つ選びました。',
    exampleMeaning: 'I chose one souvenir.',
    interactableId: 'shop-zakka-ten',
  },
  {
    id: 'v-fuurin',
    word: '風鈴',
    reading: 'ふうりん',
    meaning: 'wind chime',
    level: 'N3',
    pos: 'noun',
    example: '風鈴の音がきれいです。',
    exampleMeaning: 'The sound of the wind chime is lovely.',
    interactableId: 'shop-zakka-ten',
  },

  // ----- 銭湯 -------------------------------------------------------------
  {
    id: 'v-yu',
    word: '湯',
    reading: 'ゆ',
    meaning: 'hot water',
    level: 'N4',
    pos: 'noun',
    example: 'お湯がとてもあたたかいです。',
    exampleMeaning: 'The hot water is very warm.',
    interactableId: 'shop-sento',
  },
  {
    id: 'v-kimochi',
    word: '気持ち',
    reading: 'きもち',
    meaning: 'feeling',
    level: 'N4',
    pos: 'noun',
    example: 'おふろに入ると気持ちがいいです。',
    exampleMeaning: 'A bath feels good.',
    interactableId: 'shop-sento',
  },

  // ----- 牛の石像 ---------------------------------------------------------
  {
    id: 'v-zou',
    word: '像',
    reading: 'ぞう',
    meaning: 'statue',
    level: 'N3',
    pos: 'noun',
    example: '牛の像がまちのまんなかにあります。',
    exampleMeaning: 'A bull statue stands in the middle of the town.',
    interactableId: 'monument',
  },
  {
    id: 'v-matsuri',
    word: '祭り',
    reading: 'まつり',
    meaning: 'festival',
    level: 'N4',
    pos: 'noun',
    example: '祭りのときは像に花をそなえます。',
    exampleMeaning: 'At festival time we offer flowers to the statue.',
    interactableId: 'monument',
  },

  // ----- りんご -----------------------------------------------------------
  {
    id: 'v-akai',
    word: '赤い',
    reading: 'あかい',
    meaning: 'red',
    level: 'N4',
    pos: 'i-adj',
    example: '赤いりんごを一つもらいました。',
    exampleMeaning: 'I was given one red apple.',
    interactableId: 'prop-apple',
  },
  {
    id: 'v-kudamono',
    word: '果物',
    reading: 'くだもの',
    meaning: 'fruit',
    level: 'N4',
    pos: 'noun',
    example: '果物はからだにいいです。',
    exampleMeaning: 'Fruit is good for you.',
    interactableId: 'prop-apple',
  },

  // ----- ランタン ---------------------------------------------------------
  {
    id: 'v-akarui',
    word: '明るい',
    reading: 'あかるい',
    meaning: 'bright',
    level: 'N4',
    pos: 'i-adj',
    example: 'ランタンのあかりは明るいです。',
    exampleMeaning: "The lantern's light is bright.",
    interactableId: 'prop-brass-diya-lantern',
  },
  {
    id: 'v-akari',
    word: '灯',
    reading: 'あかり',
    meaning: 'light, lamplight',
    level: 'N3',
    pos: 'noun',
    example: 'あかりが道をてらしています。',
    exampleMeaning: 'The light is illuminating the street.',
    interactableId: 'prop-brass-diya-lantern',
  },

  // ----- 猫の石像 ---------------------------------------------------------
  {
    id: 'v-ishi',
    word: '石',
    reading: 'いし',
    meaning: 'stone',
    level: 'N4',
    pos: 'noun',
    example: '石でできたねこがいます。',
    exampleMeaning: 'There is a cat made of stone.',
    interactableId: 'prop-concrete-cat-statue',
  },
  {
    id: 'v-sawaru',
    word: '触る',
    reading: 'さわる',
    meaning: 'to touch',
    level: 'N4',
    pos: 'verb',
    example: 'ねこのあたまをそっと触りました。',
    exampleMeaning: "I gently touched the cat's head.",
    interactableId: 'prop-concrete-cat-statue',
  },
];

/** Lookup by vocabulary id. */
export const VOCABULARY_BY_ID: ReadonlyMap<string, VocabularyEntry> = new Map(
  VOCABULARY.map((entry) => [entry.id, entry]),
);

const BY_INTERACTABLE: ReadonlyMap<string, readonly VocabularyEntry[]> = (() => {
  const map = new Map<string, VocabularyEntry[]>();
  for (const entry of VOCABULARY) {
    const bucket = map.get(entry.interactableId);
    if (bucket) bucket.push(entry);
    else map.set(entry.interactableId, [entry]);
  }
  return map;
})();

/** Every word taught by one M4 interactable (empty for unknown ids). */
export function vocabularyFor(interactableId: string): readonly VocabularyEntry[] {
  return BY_INTERACTABLE.get(interactableId) ?? [];
}

/** Words of one JLPT level, in content order. */
export function vocabularyForLevel(level: JlptLevel): readonly VocabularyEntry[] {
  return VOCABULARY.filter((entry) => entry.level === level);
}
