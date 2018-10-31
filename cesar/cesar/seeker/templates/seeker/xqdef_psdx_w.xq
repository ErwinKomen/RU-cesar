(: Check whether the $ndThis node points to one of the word constructions that are defined :)
declare function tb:hasConstruction($ndThis as node()?) as xs:boolean? {

  (: Determine whether $ndThis contains the word(s) we are interested in :)
  let $bFound := 
    {% for search in search_list %}
      {% if forloop.first %}if (tb:hasW($ndThis, '{{search.single}}', {{search.line_list|safe}} )) then true()
      {% else %}else if (tb:hasW($ndThis, '{{search.single}}', {{search.line_list|safe}})) then true()
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
declare function tb:getConstructionGroup($ndThis as node()?) as xs:string? {

  (: Determine whether $ndThis contains the word(s) we are interested in :)
  let $sGroup := 
    {% for search in search_list %}
      {% if forloop.first %}if (tb:hasW($ndThis, '{{search.single}}', {{search.line_list|safe}} )) then '{{search.name}}'
      {% else %}else if (tb:hasW($ndThis, '{{search.single}}', {{search.line_list|safe}})) then '{{search.name}}'
      {% endif %}
      {% if forloop.last %}else ''{% endif %}
    {% endfor %}

  return $sGroup
};

