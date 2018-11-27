(: Check whether the $ndThis node points to one of the *EXTENDED* constructions that are defined :)
declare function tb:hasConstruction($ndThis as node()?) as xs:boolean? {

  (: Determine whether $ndThis contains the constituent(s) we are interested in :)
	let $grp := tb:getConstructionGroup($ndThis)
  let $bFound := ($grp != '')
  return $bFound
};

(: Check whether the $ndThis points to the *extended* construction $sElement :)
declare function tb:hasE($ndThis as node()?, $sSingle as xs:string?, $seqLines as item()*, 
        $sCatIncl as xs:string?, $sCatExcl as xs:string?, $sLemma as xs:string?) as xs:boolean? {

  (: Check for the single structure :)
  let $sWord := ru:word($ndThis)
  let $bIsInSingle := ($sSingle = '' or ru:matches($sWord, $sSingle))

  (: Look in the sequence of markers :)
  let $bIsInLines := some $sMulti in $seqLines satisfies ($sMulti != '' and ru:wordsmatch($ndThis, $sMulti))

	(: Look for word category :)
	let $bWord := ($bIsInSingle or $bIsInLines)

	(: Look for lemma :)
	let $ftLemma := ru:feature($ndThis, 'l')
	let $bLemma := ($sLemma = '' or ($ftLemma != '' and ru:matches($sLemma, $ftLemma) )

  (: Action depends on exclusion being defined or not :)
	let $bCategory := ( ( $sCatIncl = '' and $sCatExcl = '' ) or  
                      ( if ($sCatExcl = '') 
	                        then ru:matches($ndThis/@Label, $sCatIncl) 
												else if ($sCatIncl = '')
												  then not(ru:matches($ndThis/@Label, $sCatExcl))
	                      else ( ru:matches($ndThis/@Label, $sCatIncl) and 
       							           not(ru:matches($ndThis/@Label, $sCatExcl)) )
											)
									  )
  (: Combine all fields that *ARE* specified :)
	let $bHit := ( $bWord and $bCategory and $bLemma )

  (: Combined return :)
  return $bHit
};

(: Get the GROUP behind the *constituent* construction :)
declare function tb:getConstructionGroup($ndThis as node()?) as xs:string? {

  (: Determine whether $ndThis contains the combination of word(s)/lemma/category we are interested in :)
  let $sGroup := 
    {% for search in search_list %}
      {% if not forloop.first %}else {% endif %}if (tb:hasE($ndThis, '{{search.single}}', {{search.line_list|safe}}, '{{search.cat_incl}}', '{{search.cat_excl}}', '{{search.lemma}}' )) then '{{search.name}}'
      {% if forloop.last %}else ''{% endif %}
    {% endfor %}

  return $sGroup
};