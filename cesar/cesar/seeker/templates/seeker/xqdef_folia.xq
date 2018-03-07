declare namespace functx = "http://www.functx.com"; 
declare namespace tb = "http://www.let.ru.nl/e.komen/corpusstudio/treebank";

{% for gvar in gvar_list %}
declare variable $_{{gvar.name}} as xs:string := "{{gvar.value}}";
{% endfor %}

(: Check whether the $ndThis node points to one of the word constructions that are defined :)
declare function tb:hasConstructionW($ndThis as node()?) as xs:boolean? {

  (: Determine whether $ndThis contains the word(s) we are interested in :)
  let $bFound := 
    {% for search in search_list %}
      {% if forloop.first %}if (tb:hasW($ndThis, '{{search.single}}', {{search.line_list}} )) then true()
      {% else %}else if (tb:hasW($ndThis, '{{search.single}}', {{search.line_list}})) then true()
      {% endif %}
      {% if forloop.last %}else false(){% endif %}
    {% endfor %}

  return $bFound
};

(: Check whether the $ndThis points to the word construction $sElement :)
declare function tb:hasW($ndThis as node()?, $sSingle as xs:string?, $seqLines as item()*) as xs:boolean? {

  (: Check for the single structure :)
  let $sWord := ru:word($ndThis)
  let $bIsInSingle := ru:matches($sWord, $sSingle)

  (: Look in the sequence of markers :)
  let $bIsInLines := some $sMulti in $seqLines satisfies ru:wordsmatch($ndThis, $sMulti)

  (: Combined return :)
  return ($bIsInSingle or $bIsInLines)
};

(: Get the GROUP behind the construction :)
declare function tb:getConstructionWgroup($ndThis as node()?) as xs:string? {

  (: Determine whether $ndThis contains the word(s) we are interested in :)
  let $sGroup := 
    {% for search in search_list %}
      {% if forloop.first %}if (tb:hasW($ndThis, '{{search.single}}', {{search.line_list}} )) then '{{search.name}}'
      {% else %}else if (tb:hasW($ndThis, '{{search.single}}', {{search.line_list}})) then '{{search.name}}'
      {% endif %}
      {% if forloop.last %}else ''{% endif %}
    {% endfor %}

  return $sGroup
};

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
  (: At least get the search word :)
  let $ft_search := ru:word($search)
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
