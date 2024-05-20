/** @format */

"https://www.bqxs520.com/load.html?v1#42636-46544172-112582839-0";



第一级列表页：https://o.bqxs520.com/book/87_4750604_58373680.shtml 

真实列表页：https://o.bqxs520.com/read/Chapter/4750604.js?token=4aa05a38879a54ba9f3e941b0d437272

初步文章内容页面：https://www.bqxs520.com/load.html?v1#4750604-58373680-192057484-0  无用

https://www.bqxs520.com/read/Content/192057484.js?token=7a52230817b477f0e46837d700aed96a&t=1703476548715
https://www.bqxs520.com/read/Content/192057484.js?token=bc999ac06d261be5f03eda13499dc853&t=1703479013441

加密文章内容页面 第34章（192057484）：https://www.bqxs520.com/read/Content/192057484.js?token=bc999ac06d261be5f03eda13499dc853&t=1703476764707



https://www.bqxs520.com/read/Content/192057484.js?token=7a52230817b477f0e46837d700aed96a&t=1703490428522

https://txt.yqkfqrc.com/192057484.txt?Expires=1703489882&OSSAccessKeyId=c28ofzdk6m9w8qi53yx70vc4&Signature=UxrwNzClkQyZTYrr5%2BwU6e1mKZo%3D&response-content-encoding=gbk&t=1703489864624


/** 搜索 */

function functionName(config, params, result)
{
    let list = [];
    let regex = /\/(\d+)_(\d+)_(\d+)\.shtml/;
    for (var i = 0; i < result.list.length; i++) {
        let bookInfo = {};
        tem = regex.exec(result.list[i]["detailUrl"]);
        token = CryptoJS.HmacMD5(tem[2], tem[2]);
		bookInfo.detailUrl = "https://o.bqxs520.com/read/Chapter/" + tem[2] + ".js?token="+token;
        bookInfo.bookName = result.list[i]["bookName"];
        bookInfo.desc = result.list[i]["desc"];
        bookInfo.cover = result.list[i]["cover"];
        bookInfo.bookId = tem[2];
		list.push(bookInfo);
    }

    return { list: list };
}

/** 获取文章地址列表 */

function functionName(config, params, result) {
    let list = [];
    let reg = /<\s*a\s+onclick="read\((.*?)\)">(.*?)<\/a>/gim;
    
    while (tem = reg.exec(result)) {
        let chapterInfo = {};
        chapterInfo.title = tem[2];
        token = CryptoJS.HmacMD5(tem[1], config.httpHeaders["User-Agent"]).toString();
        t = new Date().valueOf();
        chapterInfo.url = "https://www.bqxs520.com/read/Content/" + tem[1] + ".js?token=" + token + "&t=" + t;
        chapterInfo.token = token;
        list.push(chapterInfo);
    }

    return { list: list };
}

/* 无用 */
function functionName(config, params, result)
{
    let list = [];
    crypto_code = ""
    let reg = /<\s*a\s+onclick="read\((.*?)\)">(.*?)<\/a>/gim;
    let regex = /\/(\d+)_(\d+)_(\d+)\.shtml/;
    tem1 = regex.exec(params.queryInfo.detailUrl);
    while ((tem = reg.exec(result))) {
        let chapterInfo = {};
        chapterInfo.title = tem[2];
        result = CryptoJS.HmacMD5(tem1[2], tem1[2]);
        chapterInfo.url = "https://www.bqxs520.com/load.html?v1#"+tem1[2]+"-"+tem1[3]+"-"+tem[1]+"-0";
        list.push(chapterInfo);
    }

    return { list: list };
}

function functionName(config, params, result) {
    let list = [];
    if (params.lastResponse == undefined) {
        let url = "https://txt.yqkfqrc.com";
        url += CryptoJS.AES.decrypt(result, CryptoJS.enc.Utf8.parse(params.queryInfo.token.substr(0, 16)), { iv: CryptoJS.enc.Utf8.parse(params.queryInfo.token.substr(16)), mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }).toString(CryptoJS.enc.Utf8);
        url += "&t=" + new Date().valueOf();
        return {'autoRequestMore':true, 'success':true, 'more':true, 'nextPageUrl':url,'httpHeaders':config.httpHeaders, 'POST':false};
    } else {
        return {'content':result};
    }
}

// 调用两次
function functionName(config, params, result) {
    let list = [];
    if (params.lastResponse == undefined) {
        let url = "https://txt.yqkfqrc.com";
        url += CryptoJS.AES.decrypt(result, CryptoJS.enc.Utf8.parse(params.queryInfo.token.substr(0, 16)), { iv: CryptoJS.enc.Utf8.parse(params.queryInfo.token.substr(16)), mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }).toString(CryptoJS.enc.Utf8);
        url += "&t=" + new Date().valueOf();
        return {'autoRequestMore':true, 'success':true, 'more':true, 'nextPageUrl':url,'httpHeaders':config.httpHeaders, 'POST':false};
    } else {
        return {'content':result};
    }
}



function functionName(config, params, result)
{
    let list = [];
    let regex = /"([^"]+)">([^<]+)<\/a>[\s\S]*?<td class="odd">([^<]+)<\/td>/gim;

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

/////////////视频

// 章节列表
function functionName(config, params, result) {
    let list = [];
    xpath = "//meta[@id=\"dooplay-ajax-counter\"]/@data-postid";
    xresult = params.nativeTool.XPathParserWithSource(result);
    let txt_xpath = xresult.queryWithXPath(xpath);
    for (i in txt_xpath) {
        postid = txt_xpath[i].content();
        let chapterInfo = {};
        chapterInfo.title = "hls";
        chapterInfo.url = url = config.host + "/artplayer?mvsource=0&id=" + postid + "&type=hls";
        list.push(chapterInfo);
    }

    return { list: list };
}

// 获取流地址
function functionName(config, params, result) {
    let regex = /url:'([^']+\.(?:m3u8|mp4))'/;
    let url = "";
    let match = result.match(regex);
    params.nativeTool.log(match);
    if (match && match[1]) {
        url = match[1];
    }
    return url;
}

//meta[@id="dooplay-ajax-counter"]/@data-postid || @js: return params.responseUrl + "/wp-json/dooplayer/v1/post/" + result + "?type=movie&source=1";