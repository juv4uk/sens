-- Lua 5.1-compatible source: shared by Lua and LuaJIT.
local function fib(n)
  if n < 2 then return n end
  return fib(n - 1) + fib(n - 2)
end

local function sieve(n)
  local comp = {}
  for i = 0, n do comp[i] = false end
  local i = 2
  while i * i <= n do
    if not comp[i] then
      local j = i * i
      while j <= n do
        comp[j] = true
        j = j + i
      end
    end
    i = i + 1
  end
  local count = 0
  local k = 2
  while k <= n do
    if not comp[k] then count = count + 1 end
    k = k + 1
  end
  return count
end

local function collatz(n)
  local total = 0
  local i = 1
  while i <= n do
    local x = i
    while x ~= 1 do
      if x % 2 == 0 then
        x = math.floor(x / 2)
      else
        x = 3 * x + 1
      end
      total = total + 1
    end
    i = i + 1
  end
  return total
end

local fibN = tonumber(arg[1]) or 35
local sieveN = tonumber(arg[2]) or 10000000
local colN = tonumber(arg[3]) or 1000000

print("fib(" .. fibN .. ") = " .. fib(fibN))
print("sieve(" .. sieveN .. ") = " .. sieve(sieveN))
print("collatz(" .. colN .. ") = " .. collatz(colN))
