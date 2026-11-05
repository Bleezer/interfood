const test = require('node:test');
const assert = require('node:assert/strict');
const core = require('../core.js');

test('next week follows Budapest date and ISO year', () => {
  assert.equal(core.nextWeek(new Date('2026-11-08T23:30:00Z')).start, '2026-11-16');
  assert.equal(core.nextWeek(new Date('2026-12-31T12:00:00Z')).week, 1);
  assert.equal(core.nextWeek(new Date('2026-12-31T12:00:00Z')).start, '2027-01-04');
});

test('plan validates week, IDs, unique items, Sunday and quantity', () => {
  const expected = core.nextWeek(new Date('2026-11-05T10:00:00Z'));
  const valid = {version: 1, week_start: expected.start, items: [
    {id: 1, date: '2026-11-09', name:'Csirke', code:'E1', quantity:1}]};
  assert.equal(core.validatePlan(valid, expected), valid);
  for (const patch of [{quantity:2},{id:-1},{date:'2026-11-15'},{date:'2026-11-02'}]) {
    assert.throws(() => core.validatePlan({...valid,items:[{...valid.items[0],...patch}]},expected));
  }
  assert.throws(() => core.validatePlan({...valid,items:[valid.items[0],valid.items[0]]},expected));
  assert.throws(() => core.validatePlan({...valid,week_start:'2026-11-02'},expected));
});

test('pending, done and uncertain items are never claimed twice', () => {
  const ledger = {};
  assert.equal(core.claim(ledger, 1, 20), true);
  assert.equal(core.claim(ledger, 1, 21), false);
  core.finish(ledger,1,20,'done');
  assert.equal(core.claim(ledger, 1, 20), false);
  assert.equal(core.claim(ledger,2,20),true);
  core.finish(ledger,2,20,'uncertain');
  assert.equal(core.claim(ledger,2,21),false);
  assert.throws(()=>core.finish(ledger,1,21,'done'));
});

test('ledger keys separate accounts and weeks', () => {
  assert.notEqual(core.ledgerKey('12','2026-11-09'),core.ledgerKey('13','2026-11-09'));
  assert.notEqual(core.ledgerKey('12','2026-11-09'),core.ledgerKey('12','2026-11-16'));
});
