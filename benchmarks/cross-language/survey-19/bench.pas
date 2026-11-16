program bench;

{$mode objfpc}{$H+}

uses
  SysUtils;

function Fib(n: Int64): Int64;
begin
  if n < 2 then
    Result := n
  else
    Result := Fib(n - 1) + Fib(n - 2);
end;

function Sieve(n: Int64): Int64;
var
  comp: array of Byte;
  i, j, k, count: Int64;
begin
  SetLength(comp, n + 1);
  FillChar(comp[0], n + 1, 0);
  i := 2;
  while i * i <= n do
  begin
    if comp[i] = 0 then
    begin
      j := i * i;
      while j <= n do
      begin
        comp[j] := 1;
        Inc(j, i);
      end;
    end;
    Inc(i);
  end;
  count := 0;
  k := 2;
  while k <= n do
  begin
    if comp[k] = 0 then Inc(count);
    Inc(k);
  end;
  Result := count;
end;

function Collatz(n: Int64): Int64;
var
  total, i, x: Int64;
begin
  total := 0;
  i := 1;
  while i <= n do
  begin
    x := i;
    while x <> 1 do
    begin
      if x mod 2 = 0 then
        x := x div 2
      else
        x := 3 * x + 1;
      Inc(total);
    end;
    Inc(i);
  end;
  Result := total;
end;

function ArgDef(idx: Integer; def: Int64): Int64;
begin
  if ParamCount >= idx then
    Result := StrToInt64Def(ParamStr(idx), def)
  else
    Result := def;
end;

var
  fibN, sieveN, colN: Int64;
begin
  fibN := ArgDef(1, 35);
  sieveN := ArgDef(2, 10000000);
  colN := ArgDef(3, 1000000);
  WriteLn('fib(', fibN, ') = ', Fib(fibN));
  WriteLn('sieve(', sieveN, ') = ', Sieve(sieveN));
  WriteLn('collatz(', colN, ') = ', Collatz(colN));
end.
