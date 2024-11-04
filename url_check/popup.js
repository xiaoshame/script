document.addEventListener('DOMContentLoaded', function () {
  const bookmarksList = document.getElementById('bookmarks');

  function createBookmarkNode(bookmark, isValid) {
    if (!isValid) {
      // 创建一个列表项和锚点以显示书签信息
      const li = document.createElement('li');
      const anchor = document.createElement('a');
      anchor.href = bookmark.url;
      anchor.textContent = `${bookmark.title} (${bookmark.url})`;
      anchor.target = '_blank';
      li.appendChild(anchor);

      // 创建删除按钮
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = 'Delete';
      deleteBtn.onclick = () => deleteBookmark(bookmark.id, li);
      li.appendChild(deleteBtn);

      return li;
    }
    return null;
  }

  function deleteBookmark(bookmarkId, li) {
    // 调用 Chrome 的书签 API 删除书签
    chrome.bookmarks.remove(bookmarkId, function() {
      bookmarksList.removeChild(li);
    });
  }

  function checkBookmarkValidity(url, callback) {
    fetch(url, { method: 'HEAD' })
      .then(response => {
        if (response.status == 404 || response.status == 500) {
          callback(false);
        }else{
          callback(true);
        }
      })
      .catch(() => {
        callback(false); // 请求失败认为无效
      });
  }

  function traverseBookmarks(bookmarkTreeNodes, parentElement) {
    bookmarkTreeNodes.forEach((bookmark) => {
      if (bookmark.children) {
        // 创建目录节点
        const folderLi = document.createElement('li');
        folderLi.textContent = bookmark.title;
        const ul = document.createElement('ul');
        folderLi.appendChild(ul);
        parentElement.appendChild(folderLi);
        // 递归遍历子书签
        traverseBookmarks(bookmark.children, ul);
      } else if (bookmark.url) {
        checkBookmarkValidity(bookmark.url, (isValid) => {
          const bookmarkNode = createBookmarkNode(bookmark, isValid);
          if (bookmarkNode) {
            parentElement.appendChild(bookmarkNode);
          }
        });
      }
    });
  }

  chrome.bookmarks.getTree(function(bookmarkTreeNodes) {
    traverseBookmarks(bookmarkTreeNodes, bookmarksList);
  });
});
