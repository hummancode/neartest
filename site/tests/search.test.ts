import { test } from "node:test";
import assert from "node:assert/strict";
import { fold, searchIndex, type SearchEntry } from "../src/lib/search.ts";

const IDX: SearchEntry[] = [
  { t: "Kadıköy", u: "/il/34#ilce=Kadıköy", k: "İlçe", s: "İstanbul", r: 4 },
  { t: "Kişisel enflasyon", u: "/kisisel-enflasyon", k: "Sayfa", s: "Hesapla", w: "tüfe", r: 0 },
  { t: "İstanbul", u: "/il/34-istanbul", k: "İl", s: "İstanbul · plaka 34", w: "34", r: 2 },
  { t: "İzmir", u: "/il/35-izmir", k: "İl", s: "Ege", w: "35", r: 2 },
  { t: "Merkez (Kilis)", u: "/il/79-kilis#ilce=Merkez", k: "İlçe", s: "Kilis", r: 4 },
];

test("fold is Turkish-aware and accent-insensitive", () => {
  assert.equal(fold("İSTANBUL"), "istanbul");
  assert.equal(fold("KADIKÖY"), "kadikoy");
  assert.equal(fold("Hakkâri"), "hakkari");
  assert.equal(fold("  Kişisel—enflasyon "), "kisisel enflasyon");
});

test("search matches word starts across fields, ranks title prefix first", () => {
  assert.deepEqual(searchIndex(IDX, "kadikoy").map((e) => e.t), ["Kadıköy"]);
  assert.deepEqual(searchIndex(IDX, "tufe").map((e) => e.t), ["Kişisel enflasyon"]);      // keyword
  assert.equal(searchIndex(IDX, "ist")[0].t, "İstanbul");                                    // title prefix beats subtitle
  assert.deepEqual(searchIndex(IDX, "merkez kilis").map((e) => e.t), ["Merkez (Kilis)"]);   // all words must match
  assert.deepEqual(searchIndex(IDX, "35").map((e) => e.t), ["İzmir"]);                       // plate number
  assert.deepEqual(searchIndex(IDX, "xyz"), []);
  assert.ok(searchIndex(IDX, "").every((e) => e.k === "Sayfa"));                              // empty query: pages
});
