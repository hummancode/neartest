import { test } from "node:test";
import assert from "node:assert/strict";
import { parseAmount } from "../src/lib/card.ts";

test("parseAmount accepts Turkish formats", () => {
  assert.equal(parseAmount("1.000"), 1000);
  assert.equal(parseAmount("1000"), 1000);
  assert.equal(parseAmount("1.000.000"), 1_000_000);
  assert.equal(parseAmount("2.500,50"), 2500.5);
  assert.equal(parseAmount("2500,5"), 2500.5);
  assert.equal(parseAmount("1 000 TL"), 1000);
  assert.equal(parseAmount("12.5"), 12.5); // not a thousands pattern -> decimal point
});

test("parseAmount rejects bad input", () => {
  for (const s of ["", "abc", "0", "-5", "1,2,3", "1e20", "1.00.0"]) assert.equal(parseAmount(s), null, s);
});
