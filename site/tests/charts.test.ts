import { test } from "node:test";
import assert from "node:assert/strict";
import { squarify, foldParts } from "../src/lib/charts2.ts";

test("squarify: areas proportional to values and inside the box", () => {
  const vals = [6, 6, 4, 3, 2, 2, 1];
  const rects = squarify(vals, 0, 0, 600, 400);
  const total = vals.reduce((a, b) => a + b, 0);
  rects.forEach((r, k) => {
    assert.ok(Math.abs(r.w * r.h - (vals[k] / total) * 600 * 400) < 1e-6);
    assert.ok(r.x >= -1e-9 && r.y >= -1e-9 && r.x + r.w <= 600 + 1e-6 && r.y + r.h <= 400 + 1e-6);
  });
  assert.ok(Math.abs(rects.reduce((a, r) => a + r.w * r.h, 0) - 600 * 400) < 1e-6);
});

test("foldParts keeps the top 5 and folds the rest into Diğer", () => {
  const parts = foldParts([1, 9, 3, 7, 5, 2, 8].map((v, k) => ({ name: String(k), value: v })));
  assert.equal(parts.length, 6);
  assert.deepEqual(parts.map((p) => p.value), [9, 8, 7, 5, 3, 3]);
  assert.equal(parts[5].name, "Diğer");
});
