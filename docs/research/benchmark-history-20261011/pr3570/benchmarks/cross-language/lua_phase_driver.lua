-- #1547 phase driver for Lua 5.4 source/precompiled chunk load.
-- Program chunks define a global bench() but never call it themselves.

local path = arg[1]
local mode = arg[2]
local repeats = tonumber(arg[3] or "1")

if not path or not mode then
  io.stderr:write("usage: lua_phase_driver.lua PROGRAM load|ready|repeat|full [REPEATS]\n")
  os.exit(2)
end

local chunk, err = loadfile(path)
if not chunk then
  error(err)
end

if mode == "load" then
  _G.__sens_black_box_chunk = chunk
  return
end

chunk()

if mode == "ready" then
  return
end

if type(bench) ~= "function" then
  error("program did not define global bench()")
end

if mode == "full" then
  local result = bench()
  print(result)
  _G.__sens_black_box_result = result
  return
end

if mode ~= "repeat" then
  error("unknown mode: " .. tostring(mode))
end

if not repeats or repeats < 1 then
  error("REPEATS must be >= 1")
end

local result = nil
for _ = 1, repeats do
  result = bench()
end
_G.__sens_black_box_result = result
