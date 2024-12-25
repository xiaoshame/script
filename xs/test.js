// const originalString = `"在澳门路环石排湾郊野公园大熊猫馆，大熊猫“开开”“心心”和它们的双胞胎孩子“健健”“康康”享受着快乐生活。今年是澳门回归祖国25周年，也是“开开”“心心”...`;

// function replaceQuotes(str) {
//     let tmp = str.replace(/[“”"]/g, "'");
//     return tmp;
// }
  
// const resultString = replaceQuotes(originalString);
  
// console.log(resultString);
const CryptoJS = require("crypto-js");

function aesDecrypt(data){
    let key = CryptoJS.enc.Base64.parse("ZjA0MWM0OTcxNGQzOTkwOA==")
    console.log(key);
    let iv = CryptoJS.enc.Base64.parse("MDEyMzQ1Njc4OWFiY2RlZg==");
    console.log(iv);
    let decrypted = CryptoJS.AES.decrypt(data,key, {
                    iv: iv,
                    mode: CryptoJS.mode.CBC,
                    padding: CryptoJS.pad.Pkcs7});   
    return decrypted.toString(CryptoJS.enc.Utf8)
}

let url = aesDecrypt("Y+cjw5ibDu5dlzYPEE8bmARjEIaa1uloLQpWFQfzC5XnDqnFRSKUM7+5tmE3bT64");

console.log(url);