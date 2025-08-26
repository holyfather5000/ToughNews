fetch('articles.json')
  .then(res => res.json())
  .then(data => {
    const container = document.getElementById('adminList');
    data.forEach((article, i) => {
      const div = document.createElement('div');
      div.innerHTML = `<input type="checkbox" id="chk${i}" ${article.shown ? 'checked' : ''}> ${article.title}`;
      container.appendChild(div);
      document.getElementById(`chk${i}`).addEventListener('change', (e) => {
        article.shown = e.target.checked;
      });
    });

    document.getElementById('saveBtn').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(data, null, 2)], {type : 'application/json'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'articles.json';
      a.click();
    });
  });

  fetch('articles.json')
  .then(res => res.json())
  .then(data => {
    const container = document.getElementById('articles');
    data.filter(a => a.shown).forEach(article => {
      const div = document.createElement('div');
      div.innerHTML = `
        <h3>${article.title}</h3>
        <p>${article.source}</p>
        <a href="${article.link}" target="_blank">Read more</a>
        ${article.image ? `<img src="${article.image}" width="200">` : ''}
      `;
      container.appendChild(div);
    });
  });
