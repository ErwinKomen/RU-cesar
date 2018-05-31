declare namespace functx = "http://www.functx.com"; 
declare namespace tb = "http://www.let.ru.nl/e.komen/corpusstudio/treebank";

{% for gvar in gvar_list %}
declare variable $_{{gvar.name}} as xs:string := "{{gvar.value}}";
{% endfor %}

{% if targetType == 'w' %}
	{% include 'seeker/xqdef_folia_w.xq' %}
{% else %}
	{% include 'seeker/xqdef_folia_c.xq' %}
{% endif %}

(: ----------------------------------------------
    Name: foliaw
    Goal: Get the <w> constituent that has the same id 
		      as the [ndThis] <wref> that we receive
   ---------------------------------------------- :)
declare function tb:foliaw($ndThis as node()?) as node()? {
  let $sId := $ndThis/@id
	return $ndThis/ancestor::s/descendant::w[@xml:id = $sId]
};

{% for item in dvar_list %}    {% for cvar in item.cvar_list %} {% if cvar.type == "calc" %}
(: ----------------------------------------
   Name: {{cvar.fname}}
   Goal: calculate value for variable {{item.name}}, searchgroup {{cvar.grp}}
   ---------------------------------------- :)
declare function {{cvar.fname}}($search {% if cvar.dvars|length > 0 %}, {% endif %} {{cvar.dvars}}) {
  {{cvar.code|safe}}
};
{% endif %} {% endfor %}  {% endfor %}

{% for item in feature_list %}
{% if item.type == 'func' %}
(: ----------------------------------------
   Name: {{item.fname}}
   Goal: calculate feature {{item.name}}
   ---------------------------------------- :)
declare function {{item.fname}}($search {% if dvar_all|length > 0 %}, {% endif %}{{dvar_all}}) {
  {{item.code|safe}}
};
{% endif %}
{% endfor %}


(: ----------------------------------------------
    Name: getFtList
    Goal: Create a list of features
   ---------------------------------------------- :)
declare function tb:getFtList($search, $searchgroup
      {% for item in dvar_list %}
        , ${{item.name}}{% endfor %}
      ) as xs:string? {
  (: At least get the search text and the search POS :)
  let $ft_search := ru:NodeText($search, 'clean')
  let $ft_search_pos := $search/@class
  (: Include the user-specified features here :)
  {% for feat in feature_list %}
  let $ft_{{feat.name}} := {% if feat.type == 'dvar' %}${{feat.dvar.name}}{% else %}{{feat.fname}}($search {% if dvar_all|length > 0 %}, {% endif %} {{dvar_all}}) {% endif %}
  {% endfor %}

  return concat($ft_search, ';', $ft_search_pos
  {% for feat in feature_list %}
    , ';', $ft_{{feat.name}}
  {% endfor %}
  )
};
