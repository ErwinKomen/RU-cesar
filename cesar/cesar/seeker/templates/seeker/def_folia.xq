declare namespace functx = "http://www.functx.com"; 
declare namespace tb = "http://www.let.ru.nl/e.komen/corpusstudio/treebank";

{% for gvar in gvar_list %}
  declare variable $_{{gvar.name}} as xs:string := "{{gvar.value}}";
{% endfor %}

(: Check whether   :)
declare function tb:hasConstructionW($ndThis as node()?) as xs:boolean?
{
  (: Determine whether $ndThis contains the word(s) we are interested in :)
  let $bFound := 
    {% for search in search_list %}
      {% if forloop.first %}if (tb:hasW($ndThis, '{{search.value}}')) then true
      {% elif forloop.last %}else false
      {% else %}else if (tb:hasW($ndThis, '{{search.value}}')) then true
      {% endif %}
    {% endfor %}

  return $bFound
}

declare function tb:hasW($ndThis as node()?) as xs:boolean?
{


}