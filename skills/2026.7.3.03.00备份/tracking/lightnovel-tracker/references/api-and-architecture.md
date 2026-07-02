# lightnovel.cn API & Architecture Reference

## Domain redirects

| Source | Redirects to | Notes |
|--------|-------------|-------|
| `lightnovel.cn` | `lightnovel.fun` | Main domain, SSR works here |
| `lightnovel.us` | (self, Cloudflare) | JS challenge required, unusable with curl |
| `lightnovel.fun` | (self) | API host, auth-gated |

## Webpack chunk map

From the bootstrap (`510d5ee259a95eec8de9.js`):

| Chunk ID | Filename | Content |
|----------|----------|---------|
| 0 | `102aa6c950990fb68c18.js` | ? |
| 1 | `2b67c524b228702a2f71.js` | ? |
| 2 | `62ff29f49362eb35c064.js` | ? |
| 6 | `8956df109f3e519c0e68.js` | ? |
| 13 | `6f7d2368a5560c206988.js` | Homepage components, swiper, `/api/recom/get-pc-home` |
| 23 | `caba53456728c824d9bd.js` | ? |

## API discovery

The chunk `b4bd28379f024a47d9fd.js` (chunk ID from hash, ~150KB compressed) contains the API module definitions:

```javascript
// Module 123 exports:
var r = {};  // getRecommends, getTalks, getRanks
var o = {};  // getCategories, getArticleByCates, getArticleByCate

var c = "/api/recom/get-recommends";
var l = "/api/recom/get-talks";
var d = "/api/recom/get-ranks";
var m = "/api/category/get-categories";
var h = "/api/category/get-article-cates";
var v = "/api/category/get-article-by-cate";

// Module 128 exports:
var r = "/api/search/search-result";
var o = "/api/search/get-search-tags";
```

Other APIs found in the same chunk:
- `/api/captcha/recaptcha-generate`
- `/api/captcha/email`
- `/api/user/check-nickname`
- `/api/user/register`
- `/api/user/login`
- `/api/user/info`
- `/api/user/follow`
- `/api/user/get-articles`
- `/api/user/get-series`
- `/api/notify/unread`
- `/api/notify/dynamic`
- `/api/msg/get-reply-msg`
- `/api/smiley/get-list`
- `/api/history/add-collection`
- `/api/history/del-collection`
- `/api/history/get-collections`
- `/api/history/get-history`
- `/api/history/del-history`
- `/api/article/get-config`

## NUXT parameter mapping

From the homepage SSR function call arguments (61 params):

```
a=0, b=1, c=default_cover_url, d="", e=2, f=13, g=12, h=3, i=4,
j=11, k=10, l=6, m=8, n=5, o=9, p=33, q=false, r=62,
s="輕小說", t="其它", u="轉載", v=null, w=1142232,
x=article_title, y=hits_count, z=60,
A=1143334, B=10280, C=1139274, D=15998, E=1144435, F=1033631,
G=article_title, H=1981, I=258638, J=7, K=1137459, L=63,
M=122, N=15, O=111, P=2172, Q=115, R=1144495, S=2133, T=60,
U="漫畫", V="動畫", W="遊戲", X=4809, Y="下載", Z="原創",
_="發佈", $="資訊", aa=34, ab=36, ac=37, ad=40, ae="更多", af="tc", ag=14
```

Key mappings:
- **gid (group id)**: `f=13` = 轻小说, `g=12` = 资讯, `j=11` = ?
- **cover_type**: `a=0` = text article, `b=1` = image/cover article
- **type in rows**: `e=2` = 轻小说 section type

## Homepage data structure

```javascript
{
  layout: "default",
  data: [{
    carousel: [{id, type, title, action_params(aid), pic_url, group_id, comments, hits}],
    recommends: [{id, type, title, action_params(aid), pic_url, group_id, comments, hits}],
    rows: [{
      gid,           // group ID
      icon,          // section icon URL
      type,          // section type
      title,         // section name
      more,          // "更多" text
      more_type,     // 1 = internal link
      more_params,   // "fid,typeid,page"  eg "3,106,1" for 日轻韩轻
      ranks: [{rank, aid, title, cover, comments, hits, cover_type, time, sid, series_name, banner}],
      items: [{id, type, title, action_type, action_params(aid), pic_url, group_id, comments, hits}]
    }]
  }],
  fetch: [],
  error: null,
  state: {
    locales, locale, profile, category, home, login, msg, emoji, user, ...
  },
  serverRendered: true,
  routePath: "/"
}
```

## Light novel category params

- **fid**: 3 (forum ID)
- **typeid**: 106 (subcategory for 日轻/韩轻 translations)
- **gid**: 13 (group ID for 轻小说 in the homepage rows)
- **URL**: `https://www.lightnovel.cn/category/3/106`
