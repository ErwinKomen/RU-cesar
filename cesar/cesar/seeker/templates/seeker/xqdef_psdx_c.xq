(: Check whether the $ndThis node points to one of the *constituent* constructions that are defined :)
declare function tb:hasConstruction($ndThis as node()?) as xs:boolean? {

  (: Determine whether $ndThis contains the constituent(s) we are interested in :)
	let $grp := tb:getConstructionGroup($ndThis)
  let $bFound := ($grp != '')
  return $bFound
};

(: Check whether the $ndThis points to the *constituent* construction $sElement :)
declare function tb:hasC($ndThis as node()?, $sCatIncl as xs:string?, $sCatExcl as xs:string?) as xs:boolean? {

  (: Action depends on exclusion being defined or not :)
	let $bHit := if ($sCatExcl = '') 
	             then ru:matches($ndThis/@Label, $sCatIncl)
	             else ( ru:matches($ndThis/@Label, $sCatIncl) and 
							        not(ru:matches($ndThis/@Label, $sCatExcl))
										)
  (: Combined return :)
  return $bHit
};

(: Get the GROUP behind the *constituent* construction :)
declare function tb:getConstructionGroup($ndThis as node()?) as xs:string? {

  (: Determine whether $ndThis contains the word(s) we are interested in :)
  let $sGroup := 
    {% for search in search_list %}
      {% if forloop.first %}if (tb:hasC($ndThis, '{{search.cat_incl}}', '{{search.cat_excl}}' )) then '{{search.name}}'
      {% else %}else if (tb:hasC($ndThis, '{{search.cat_incl}}', '{{search.cat_excl}}')) then '{{search.name}}'
      {% endif %}
      {% if forloop.last %}else ''{% endif %}
    {% endfor %}

  return $sGroup
};
