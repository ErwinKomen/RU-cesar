<FoLiA>{
    (: This main query is meant for FOLIA encoding :)
    
    for $search in //su[tb:hasConstructionW(self::su)]
    
      (: Get the group this construction belongs to :)
      let $searchgroup := tb:getConstructionWgroup($search)
      
      (: Iterate over all the definition variables :)
      {% for item in dvar_list %}
        let ${{item.name}} := 
          {% for cvar in item.cvar_list %}
            {% if forloop.first %}
              if ($searchgroup = '{{cvar.grp}}') then {{cvar.code|safe}}
            {% elif forloop.last %}
              else {{cvar.code|safe}}
            {% else %}
              else if ($searchgroup = '{{cvar.grp}}') then {{cvar.code|safe}}
            {% endif %}
          {% endfor %}
      {% endfor %}
    
    (: Divide the results over the search group :)
    let $cat := $searchgroup
    
    (: Calculate the features :)
    let $dbList := tb:getFtList($search, $searchgroup
      {% for item in dvar_list %}, ${{item.name}}{% endfor %})
    
    (: Conditions that must hold :)
    where (
      {% for cond in cond_list %}
        {% if not forloop.first %}and {% endif %} ({{cond|safe}})
      {% endfor %}
    )
    
    (: Return the results :)
    return ru:back($search, $dbList, $cat)
  }
</FoLiA>