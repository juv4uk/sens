"use strict";

const fs = require("fs");

function nowNs() {
  return process.hrtime.bigint();
}

function moduleBytes(path) {
  return fs.readFileSync(path);
}

function compileOne(bytes) {
  const started = nowNs();
  const mod = new WebAssembly.Module(bytes);
  const elapsed = nowNs() - started;
  return { mod, elapsedNs: Number(elapsed) };
}

function instantiateOne(mod) {
  const started = nowNs();
  const instance = new WebAssembly.Instance(mod);
  const elapsed = nowNs() - started;
  return { instance, elapsedNs: Number(elapsed) };
}

function main() {
  if (process.argv.length < 4 || process.argv.length > 5) {
    throw new Error(
      "usage: node wasm_control.js <module.wasm> <preflight|compile|instantiate|call|cold> [repeat]"
    );
  }

  const path = process.argv[2];
  const mode = process.argv[3];
  const repeat = process.argv.length === 5 ? Number(process.argv[4]) : 1;
  if (!Number.isInteger(repeat) || repeat <= 0) {
    throw new Error("repeat must be a positive integer");
  }

  const bytes = moduleBytes(path);

  if (mode === "preflight") {
    const mod = new WebAssembly.Module(bytes);
    const instance = new WebAssembly.Instance(mod);
    console.log(`VALUE=${instance.exports.run()}`);
    console.log("ELAPSED_NS=0");
    return;
  }

  if (mode === "compile") {
    const { elapsedNs } = compileOne(bytes);
    console.log(`ELAPSED_NS=${elapsedNs}`);
    return;
  }

  if (mode === "instantiate") {
    const mod = new WebAssembly.Module(bytes);
    const { elapsedNs } = instantiateOne(mod);
    console.log(`ELAPSED_NS=${elapsedNs}`);
    return;
  }

  if (mode === "call") {
    const mod = new WebAssembly.Module(bytes);
    const instance = new WebAssembly.Instance(mod);
    let last = 0;
    const started = nowNs();
    for (let i = 0; i < repeat; i += 1) {
      last = instance.exports.run();
    }
    const elapsed = nowNs() - started;
    console.log(`VALUE=${last}`);
    console.log(`ELAPSED_NS=${Number(elapsed)}`);
    return;
  }

  if (mode === "cold") {
    const started = nowNs();
    const mod = new WebAssembly.Module(bytes);
    const instance = new WebAssembly.Instance(mod);
    const value = instance.exports.run();
    const elapsed = nowNs() - started;
    console.log(`VALUE=${value}`);
    console.log(`ELAPSED_NS=${Number(elapsed)}`);
    return;
  }

  throw new Error(`unknown mode: ${mode}`);
}

main();
