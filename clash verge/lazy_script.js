const regionOptions = {
    regions: [
        {
            name: 'HK香港',
            regex: /港|🇭🇰|hk|hongkong|hong kong/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/Hong_Kong.png',
        },
        {
            name: 'US美国',
            regex: /美|🇺🇸|us|united state|america/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/United_States.png',
        },
        {
            name: 'JP日本',
            regex: /日本|🇯🇵|jp|japan/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/Japan.png',
        },
        {
            name: 'KR韩国',
            regex: /韩|🇰🇷|kr|korea/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/Korea.png',
        },
        {
            name: 'SG新加坡',
            regex: /新加坡|🇸🇬|sg|singapore/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/Singapore.png',
        },
        {
            name: 'CN中国大陆',
            regex: /中国|🇨🇳|cn|china/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/China_Map.png',
        },
        {
            name: 'TW台湾省',
            regex: /台湾|🇹🇼|tw|taiwan|tai wan/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/China.png',
        },
        {
            name: 'GB英国',
            regex: /英|🇬🇧|uk|united kingdom|great britain/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/United_Kingdom.png',
        },
        {
            name: 'DE德国',
            regex: /德国|🇩🇪|de|germany/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/Germany.png',
        },
        {
            name: 'MY马来西亚',
            regex: /马来|🇩🇪|my|malaysia/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/Malaysia.png',
        },
        {
            name: 'TK土耳其',
            regex: /土耳其|🇹🇷|tk|turkey/i,
            ratioLimit: 2,
            icon: 'https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/Turkey.png',
        }
    ]
};

// 代理组通用配置
const proxyGroupBase = {
    type: "url-test",
    url: "http://www.gstatic.com/generate_204",
    interval: 300,
    tolerance: 50
};

function main(config) {
    // 检查配置是否有代理节点
    if (!config.proxies || config.proxies.length === 0) {
        throw new Error("配置文件中未找到代理节点");
    }

    const regionGroups = [];
    let otherProxies = [...config.proxies];

    // 按地区分组
    regionOptions.regions.forEach(region => {
        const regionProxies = config.proxies.filter(proxy =>
            proxy.name.match(region.regex)
        );

        if (regionProxies.length > 0) {
            regionGroups.push({
                ...proxyGroupBase,
                name: region.name,
                proxies: regionProxies.map(p => p.name),
                icon: region.icon
            });

            // 从其他节点中移除已分组的节点
            otherProxies = otherProxies.filter(proxy =>
                !regionProxies.includes(proxy)
            );
        }
    });

    // 添加其他未分组节点
    if (otherProxies.length > 0) {
        regionGroups.push({
            ...proxyGroupBase,
            name: "其他节点",
            proxies: otherProxies.map(p => p.name),
            icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/World_Map.png"
        });
    }

    // 添加自动选择组
    const allGroups = ["自动选择", ...regionGroups.map(g => g.name)];
    config["proxy-groups"] = [
        {
            name: "自动选择",
            type: "url-test",
            proxies: regionGroups.map(g => g.name),
            url: "http://www.gstatic.com/generate_204",
            interval: 300,
            icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure/IconSet/Color/Auto.png"
        },
        ...regionGroups
    ];

    // 设置基础规则
    config.rules = [
        "GEOIP,CN,DIRECT",
        "MATCH,自动选择"
    ];

    return config;
}