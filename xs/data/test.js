const originalString = `"在澳门路环石排湾郊野公园大熊猫馆，大熊猫“开开”“心心”和它们的双胞胎孩子“健健”“康康”享受着快乐生活。今年是澳门回归祖国25周年，也是“开开”“心心”...`;

function replaceQuotes(str) {
    let tmp = str.replace(/[“”"]/g, "'");
    return tmp;
}
  
const resultString = replaceQuotes(originalString);
  
console.log(resultString);