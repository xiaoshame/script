/** @format */

// "https://www.bqxs520.com/load.html?v1#42636-46544172-112582839-0";



// 第一级列表页：https://o.bqxs520.com/book/87_4750604_58373680.shtml 

// 真实列表页：https://o.bqxs520.com/read/Chapter/4750604.js?token=4aa05a38879a54ba9f3e941b0d437272

// 初步文章内容页面：https://www.bqxs520.com/load.html?v1#4750604-58373680-192057484-0  无用

// https://www.bqxs520.com/read/Content/192057484.js?token=7a52230817b477f0e46837d700aed96a&t=1703476548715
// https://www.bqxs520.com/read/Content/192057484.js?token=bc999ac06d261be5f03eda13499dc853&t=1703479013441

// 加密文章内容页面 第34章（192057484）：https://www.bqxs520.com/read/Content/192057484.js?token=bc999ac06d261be5f03eda13499dc853&t=1703476764707



// https://www.bqxs520.com/read/Content/192057484.js?token=7a52230817b477f0e46837d700aed96a&t=1703490428522

// https://txt.yqkfqrc.com/192057484.txt?Expires=1703489882&OSSAccessKeyId=c28ofzdk6m9w8qi53yx70vc4&Signature=UxrwNzClkQyZTYrr5%2BwU6e1mKZo%3D&response-content-encoding=gbk&t=1703489864624


// /** 搜索 */

// function functionName(config, params, result)
// {
//     let list = [];
//     let regex = /\/(\d+)_(\d+)_(\d+)\.shtml/;
//     for (var i = 0; i < result.list.length; i++) {
//         let bookInfo = {};
//         tem = regex.exec(result.list[i]["detailUrl"]);
//         token = CryptoJS.HmacMD5(tem[2], tem[2]);
// 		bookInfo.detailUrl = "https://o.bqxs520.com/read/Chapter/" + tem[2] + ".js?token="+token;
//         bookInfo.bookName = result.list[i]["bookName"];
//         bookInfo.desc = result.list[i]["desc"];
//         bookInfo.cover = result.list[i]["cover"];
//         bookInfo.bookId = tem[2];
// 		list.push(bookInfo);
//     }

//     return { list: list };
// }

// /** 获取文章地址列表 */

// function functionName(config, params, result) {
//     let list = [];
//     let reg = /<\s*a\s+onclick="read\((.*?)\)">(.*?)<\/a>/gim;
    
//     while (tem = reg.exec(result)) {
//         let chapterInfo = {};
//         chapterInfo.title = tem[2];
//         token = CryptoJS.HmacMD5(tem[1], config.httpHeaders["User-Agent"]).toString();
//         t = new Date().valueOf();
//         chapterInfo.url = "https://www.bqxs520.com/read/Content/" + tem[1] + ".js?token=" + token + "&t=" + t;
//         chapterInfo.token = token;
//         list.push(chapterInfo);
//     }

//     return { list: list };
// }

// /* 无用 */
// function functionName(config, params, result)
// {
//     let list = [];
//     crypto_code = ""
//     let reg = /<\s*a\s+onclick="read\((.*?)\)">(.*?)<\/a>/gim;
//     let regex = /\/(\d+)_(\d+)_(\d+)\.shtml/;
//     tem1 = regex.exec(params.queryInfo.detailUrl);
//     while ((tem = reg.exec(result))) {
//         let chapterInfo = {};
//         chapterInfo.title = tem[2];
//         result = CryptoJS.HmacMD5(tem1[2], tem1[2]);
//         chapterInfo.url = "https://www.bqxs520.com/load.html?v1#"+tem1[2]+"-"+tem1[3]+"-"+tem[1]+"-0";
//         list.push(chapterInfo);
//     }

//     return { list: list };
// }

// function functionName(config, params, result) {
//     let list = [];
//     if (params.lastResponse == undefined) {
//         let url = "https://txt.yqkfqrc.com";
//         url += CryptoJS.AES.decrypt(result, CryptoJS.enc.Utf8.parse(params.queryInfo.token.substr(0, 16)), { iv: CryptoJS.enc.Utf8.parse(params.queryInfo.token.substr(16)), mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }).toString(CryptoJS.enc.Utf8);
//         url += "&t=" + new Date().valueOf();
//         return {'autoRequestMore':true, 'success':true, 'more':true, 'nextPageUrl':url,'httpHeaders':config.httpHeaders, 'POST':false};
//     } else {
//         return {'content':result};
//     }
// }

// // 调用两次
// function functionName(config, params, result) {
//     let list = [];
//     if (params.lastResponse == undefined) {
//         let url = "https://txt.yqkfqrc.com";
//         url += CryptoJS.AES.decrypt(result, CryptoJS.enc.Utf8.parse(params.queryInfo.token.substr(0, 16)), { iv: CryptoJS.enc.Utf8.parse(params.queryInfo.token.substr(16)), mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }).toString(CryptoJS.enc.Utf8);
//         url += "&t=" + new Date().valueOf();
//         return {'autoRequestMore':true, 'success':true, 'more':true, 'nextPageUrl':url,'httpHeaders':config.httpHeaders, 'POST':false};
//     } else {
//         return {'content':result};
//     }
// }

(function anonymous(
) {
debugger
})

function functionName(config, params, result)
{
    let list = [];
    let regex = '/<script[^>]*type="application/json">([^<]*)</script>/gim';

    params.nativeTool.log("111111111");
    while (tem = regex.exec(result)) {
        let bookInfo = {};
		    bookInfo.detailUrl = "http://www.biqu520.net" + tem[1];
        bookInfo.bookName = tem[2];
        bookInfo.author = tem[3]
		list.push(bookInfo);
    }

    return { list: list };
}

// /////////////视频

// // 章节列表
// function functionName(config, params, result) {
//     let list = [];
//     xpath = "//meta[@id=\"dooplay-ajax-counter\"]/@data-postid";
//     xresult = params.nativeTool.XPathParserWithSource(result);
//     let txt_xpath = xresult.queryWithXPath(xpath);
//     for (i in txt_xpath) {
//         postid = txt_xpath[i].content();
//         let chapterInfo = {};
//         chapterInfo.title = "hls";
//         chapterInfo.url = url = config.host + "/artplayer?mvsource=0&id=" + postid + "&type=hls";
//         list.push(chapterInfo);
//     }

//     return { list: list };
// }

// 章节列表
function functionName(config, params, result) {
    let list = [];
    xpath = '//script[@class="wp-playlist-script"]';
    xresult = params.nativeTool.XPathParserWithSource(result);
    let txt_xpath = xresult.queryWithXPath(xpath);
    for (let i in txt_xpath) {
        let chapterInfo = {};
        let jsonData = JSON.parse(txt_xpath[i].content());
        chapterInfo.title = "mp4";
        chapterInfo.url = "https://v.ddys.pro/" + jsonData.tracks[0].src0;
        list.push(chapterInfo);
    }

    return { list: list };
}

// // 获取流地址
// function functionName(config, params, result) {
//     let regex = /url:'([^']+\.(?:m3u8|mp4))'/;
//     let url = "";
//     let match = result.match(regex);
//     params.nativeTool.log(match);
//     if (match && match[1]) {
//         url = match[1];
//     }
//     return url;
// }


//meta[@id="dooplay-ajax-counter"]/@data-postid || @js: return params.responseUrl + "/wp-json/dooplayer/v1/post/" + result + "?type=movie&source=1";

//漫画章节列表
function functionName(config, params, result) {
    let list = [];
    let regex = '<script[^>]*type="application/json">([^<]*)</script>';
    // let match = result.match(regex);
    while (tem = regex.exec(result)) {
        let chapterInfo = {};
        chapterInfo.title = tem[2];
        chapterInfo.url = tem[1];
        list.push(chapterInfo);
    }
    
    return { list: list.reverse() };
}

//漫画url
function functionName(config, params, result) {
    let regex = /\(\'([^\']+)\',([^,]+),([^,]+),([^,]+),([^,]+),([^,]+)\)/gim;
    while (tem = regex.exec(result)) {
        let content = [];
        let nextre = /'([A-Za-z0-9+/=]+)'\[/gim;
        tem_k = nextre.exec(tem[4]);
        let k = splic(tem_k[1], tem_k[1].length, 32).split("|");
        data = decode(tem[1], tem[2], tem[3], k);
        let imgrex = /\((\{[\s\S]*?)\)./gim;
        let img_tem = imgrex.exec(data);
        let img_json = JSON.parse(img_tem[1]);
        let img_count = img_json.count;
        let imglist = img_json.images;
        let sl_e = img_json.sl.e;
        let sl_m = img_json.sl.m;
        for (i = 0; i < img_count; i++) {
            content[i] =
                "https://eu1.hamreus.com" +
                imglist[i] +
                "e=" +
                sl_e +
                "&m=" +
                sl_m;
        }
        // // JSON.stringify({
        //     "content": content,
        //     "httpHeaders": config.httpHeaders
        // });
        return JSON.stringify({
            "content": content.join("\n"),
            "httpHeaders": config.httpHeaders
        });
        // return { "content": content.join("\n"),"httpHeaders": config.httpHeaders};
    }
}

// function getBaseValue(alphabet, character) {
//   var baseReverseDic = {};
//   if (!baseReverseDic[alphabet]) {
//     baseReverseDic[alphabet] = {};
//     for (var i = 0; i < alphabet.length; i++) {
//       baseReverseDic[alphabet][alphabet.charAt(i)] = i;
//     }
//   }
//   return baseReverseDic[alphabet][character];
// }

// function decompressFromBase64(input, index) {
//   if (input == null) return "";
//   if (input == "") return null;
//   var keyStrBase64 =
//     "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
//   let value = getBaseValue(keyStrBase64, input.charAt(index));
//   return value;
// }

// function splic(input, length, resetValue) {
//   var f = String.fromCharCode;
//   var dictionary = [],
//     next,
//     enlargeIn = 4,
//     dictSize = 4,
//     numBits = 3,
//     entry = "",
//     result = [],
//     i,
//     w,
//     bits,
//     resb,
//     maxpower,
//     power,
//     c,
//     data = {
//       val: decompressFromBase64(input, 0),
//       position: resetValue,
//       index: 1,
//     };
//   for (i = 0; i < 3; i += 1) {
//     dictionary[i] = i;
//   }
//   bits = 0;
//   maxpower = Math.pow(2, 2);
//   power = 1;
//   while (power != maxpower) {
//     resb = data.val & data.position;
//     data.position >>= 1;
//     if (data.position == 0) {
//       data.position = resetValue;
//       data.val = decompressFromBase64(input, data.index++);
//     }
//     bits |= (resb > 0 ? 1 : 0) * power;
//     power <<= 1;
//   }
//   switch ((next = bits)) {
//     case 0:
//       bits = 0;
//       maxpower = Math.pow(2, 8);
//       power = 1;
//       while (power != maxpower) {
//         resb = data.val & data.position;
//         data.position >>= 1;
//         if (data.position == 0) {
//           data.position = resetValue;
//           data.val = decompressFromBase64(input, data.index++);
//         }
//         bits |= (resb > 0 ? 1 : 0) * power;
//         power <<= 1;
//       }
//       c = f(bits);
//       break;
//     case 1:
//       bits = 0;
//       maxpower = Math.pow(2, 16);
//       power = 1;
//       while (power != maxpower) {
//         resb = data.val & data.position;
//         data.position >>= 1;
//         if (data.position == 0) {
//           data.position = resetValue;
//           data.val = decompressFromBase64(input, data.index++);
//         }
//         bits |= (resb > 0 ? 1 : 0) * power;
//         power <<= 1;
//       }
//       c = f(bits);
//       break;
//     case 2:
//       return "";
//   }
//   dictionary[3] = c;
//   w = c;
//   result.push(c);
//   while (true) {
//     if (data.index > length) {
//       return "";
//     }
//     bits = 0;
//     maxpower = Math.pow(2, numBits);
//     power = 1;
//     while (power != maxpower) {
//       resb = data.val & data.position;
//       data.position >>= 1;
//       if (data.position == 0) {
//         data.position = resetValue;
//         data.val = decompressFromBase64(input, data.index++);
//       }
//       bits |= (resb > 0 ? 1 : 0) * power;
//       power <<= 1;
//     }
//     switch ((c = bits)) {
//       case 0:
//         bits = 0;
//         maxpower = Math.pow(2, 8);
//         power = 1;
//         while (power != maxpower) {
//           resb = data.val & data.position;
//           data.position >>= 1;
//           if (data.position == 0) {
//             data.position = resetValue;
//             data.val = decompressFromBase64(input, data.index++);
//           }
//           bits |= (resb > 0 ? 1 : 0) * power;
//           power <<= 1;
//         }
//         dictionary[dictSize++] = f(bits);
//         c = dictSize - 1;
//         enlargeIn--;
//         break;
//       case 1:
//         bits = 0;
//         maxpower = Math.pow(2, 16);
//         power = 1;
//         while (power != maxpower) {
//           resb = data.val & data.position;
//           data.position >>= 1;
//           if (data.position == 0) {
//             data.position = resetValue;
//             data.val = decompressFromBase64(input, data.index++);
//           }
//           bits |= (resb > 0 ? 1 : 0) * power;
//           power <<= 1;
//         }
//         dictionary[dictSize++] = f(bits);
//         c = dictSize - 1;
//         enlargeIn--;
//         break;
//       case 2:
//         return result.join("");
//     }
//     if (enlargeIn == 0) {
//       enlargeIn = Math.pow(2, numBits);
//       numBits++;
//     }
//     if (dictionary[c]) {
//       entry = dictionary[c];
//     } else {
//       if (c === dictSize) {
//         entry = w + w.charAt(0);
//       } else {
//         return null;
//       }
//     }
//     result.push(entry);
//     dictionary[dictSize++] = w + entry.charAt(0);
//     enlargeIn--;
//     w = entry;
//     if (enlargeIn == 0) {
//       enlargeIn = Math.pow(2, numBits);
//       numBits++;
//     }
//   }
// }

// function decode(p, a, c, k) {
//   let d = {};
//   let e = function (c) {
//     return (
//       (c < a ? "" : e(parseInt(c / a))) +
//       ((c = c % a) > 35 ? String.fromCharCode(c + 29) : c.toString(36))
//     );
//   };
//   if (!"".replace(/^/, String)) {
//     while (c--) d[e(c)] = k[c] || e(c);
//     k = [
//       function (e) {
//         return d[e];
//       },
//     ];
//     e = function () {
//       return "\\w+";
//     };
//     c = 1;
//   }
//   while (c--)
//     if (k[c]) p = p.replace(new RegExp("\\b" + e(c) + "\\b", "g"), k[c]);
//   return p;
// }

// let input =
//   'KwRgTMDMA+2DTekAchd6OmADAFke6AHAOwHNoB3AUwCM9oAXAQ3wGcYJp0Z1h2R2A2dgHZY6ROwCc0AJYBbekXJN2mdmHwAncgEkCU2tBC4N5AG5aAJtEHBBkSCoLkAHrQvQAxgAt6eWuXUAKnoANuRWwHzigmJePn7qbtCAWXKAgTmA5NaAgZGAFOqAvwmAQHqA836ApCGA0XKAhUqAAkaAIW6A7BaACtrQlAD2TQDWAHL0MmHNbW7WfKCSILwgAiAwABrApOIA+jIA8gBaAGoAigBCwSaCcwBiAF6U9OakpAaCIILiiHwgmGpMwY3BTe6tc+7u0EwMtABXJTuJoAgj6cBoVgqMC8DAGYZia7QTSnfwGbgPNBqADKAFkABJAA==';
// let k = splic(input,input.length, 32).split('|');

// data = decode(
//   'T.P({"w":0,"v":"u","s":r,"q":"2","p":o,"n":x,"h":["/7/t/6-3/0/2/b.4.5","/7/t/6-3/0/2/j.4.5","/7/t/6-3/0/2/9.4.5","/7/t/6-3/0/2/i.4.5","/7/t/6-3/0/2/a.4.5","/7/t/6-3/0/2/c.4.5","/7/t/6-3/0/2/d.4.5","/7/t/6-3/0/2/f.4.5","/7/t/6-3/0/2/g.4.5","/7/t/6-3/0/2/l.4.5","/7/t/6-3/0/2/y.4.5","/7/t/6-3/0/2/H.4.5","/7/t/6-3/0/2/A.4.5","/7/t/6-3/0/2/R.4.5","/7/t/6-3/0/2/Q.4.5","/7/t/6-3/0/2/z.4.5","/7/t/6-3/0/2/O.4.5","/7/t/6-3/0/2/N.4.5","/7/t/6-3/0/2/M.4.5","/7/t/6-3/0/2/L.4.5","/7/t/6-3/0/2/K.4.5","/7/t/6-3/0/2/S.4.5","/7/t/6-3/0/2/I.4.5","/7/t/6-3/0/2/J.4.5","/7/t/6-3/0/2/8.4.5"],"G":8,"F":1,"E":"","D":{"e":C,"m":"B"}}).k();',
//   56,56,k
// );

// console.log(data);