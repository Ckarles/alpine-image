function(inputV='0.1.0') {
  local splitV = std.splitLimit(inputV, '.', 2),
  local parsedV = [
    std.parseInt(n)
    for n in splitV
  ] + [
    0
    for i in std.range(0, 3 - std.length(splitV))
  ],
  local printV = function(from, to=from)
    std.join('.', [
      std.format('%d', parsedV[i])
      for i in std.range(from, to)
    ]),
  major: printV(0),
  minor: printV(1),
  build: printV(2),
  canonical: printV(0, 2),
  majorMinor: printV(0, 1),
}
