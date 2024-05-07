/** @format */

function decodeCont(r) {
  return (function (r) {
    var o,
      t,
      e,
      a,
      n,
      C,
      h = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
      d = "",
      f = 0;
    for (r = r.replace(/[^A-Za-z0-9\+\/\=]/g, ""); f < r.length; )
      (o =
        (h.indexOf(r.charAt(f++)) << 2) |
        ((a = h.indexOf(r.charAt(f++))) >> 4)),
        (t = ((15 & a) << 4) | ((n = h.indexOf(r.charAt(f++))) >> 2)),
        (e = ((3 & n) << 6) | (C = h.indexOf(r.charAt(f++)))),
        (d += String.fromCharCode(o)),
        64 != n && (d += String.fromCharCode(t)),
        64 != C && (d += String.fromCharCode(e));
    return (function (r) {
      for (var o, t = "", e = 0, a = 0, n = 0; e < r.length; )
        (a = r.charCodeAt(e)) < 128
          ? ((t += String.fromCharCode(a)), e++)
          : 191 < a && a < 224
          ? ((n = r.charCodeAt(e + 1)),
            (t += String.fromCharCode(((31 & a) << 6) | (63 & n))),
            (e += 2))
          : ((n = r.charCodeAt(e + 1)),
            (o = r.charCodeAt(e + 2)),
            (t += String.fromCharCode(
              ((15 & a) << 12) | ((63 & n) << 6) | (63 & o)
            )),
            (e += 3));
      return t;
    })(d);
  })(
    (r = r
      .split("")
      .map(function (r) {
        var o, t;
        return r.match(/[A-Za-z]/)
          ? ((o = Math.floor(r.charCodeAt(0) / 97)),
            (t = (r.toLowerCase().charCodeAt(0) - 83) % 26 || 26),
            String.fromCharCode(t + (0 == o ? 64 : 96)))
          : r;
      })
      .join(""))
  );
}
