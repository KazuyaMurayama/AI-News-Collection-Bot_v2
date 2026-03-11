# AIニュースダイジェスト {{ date }}

{% for story in stories %}
## 記事 {{ loop.index }}: {{ story.story_title }}

**ソース:** {{ story.source }} | **カテゴリ:** {{ story.category }} | **タグ:** {{ story.tags | join(', ') }}

**元記事:** [{{ story.title }}]({{ story.url }})

{{ story.story_body }}

---

{% endfor %}

{% if insight %}
## 本日のインサイト

{{ insight }}
{% endif %}
