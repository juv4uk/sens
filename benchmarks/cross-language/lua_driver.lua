-- Matched Lua 5.4 phase driver for #1547.
--
-- All measured Lua phases use the same source/chunk path:
--   load:   loadfile(PROGRAM), do not execute the chunk;
--   ready:  loadfile + execute chunk, do not call bench();
--   repeat: ready + call bench() N times;
--   full:   ready + call bench() once and print the result.
--
-- Each workload source returns a table with one field: bench.

local function usage()
  io.stderr:write("usage: lua_driver.lua PROGRAM.lua load|ready|repeat|full [REPEATS]\n")
  os.exit(2)
end

if #arg < 2 or #arg > 3 then
  usage()
end

local path = arg[1]
local mode = arg[2]

local function load_program()
  local chunk, err = loadfile(path, "t")
  if not chunk then
    error(err)
  end
  return chunk
end

if mode == "load" then
  _G.__sens_cross_bench_chunk = load_program()
  os.exit(0)
end

local chunk = load_program()
local module = chunk()
if type(module) ~= "table" or type(module.bench) ~= "function" then
  error("workload must return { bench = function }")
end

if mode == "ready" then
  _G.__sens_cross_bench_module = module
  os.exit(0)
end

if mode == "full" then
  print(module.bench())
  os.exit(0)
end

if mode ~= "repeat" or #arg ~= 3 then
  usage()
end

local repeats = tonumber(arg[3])
if repeats == nil or repeats < 1 or repeats % 1 ~= 0 then
  error("REPEATS must be a positive integer")
end

local result = nil
for _ = 1, repeats do
  result = module.bench()
end
_G.__sens_cross_bench_result = result
