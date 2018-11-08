<TEI>{
    (: This main query is meant for PSDX encoding :)
    
    for $search in //eTree[tb:hasConstruction(self::eTree)]
    
      (: Get the group this construction belongs to :)
      let $searchgroup := tb:getConstructionGroup($search)
      
      (: Iterate over all the definition variables :)
      {% for item in dvar_list %}
        let ${{item.name}} := 
          {% for cvar in item.cvar_list %}
            (: dvarnum = {{cvar.dvarnum}} :)
            {% if item.cvar_list|length == 1 %} 
              {% if cvar.type == "calc" %}{{cvar.fname}}($search {% if cvar.dvarnum > 0 %},{% endif %} {{cvar.dvars}}){% else %}{{cvar.code|safe}}{% endif %}
            {% elif forloop.first %}
              if ($searchgroup = '{{cvar.grp}}') then {% if cvar.type == "calc" %}{{cvar.fname}}($search {% if cvar.dvarnum > 0 %},{% endif %} {{cvar.dvars}}){% else %}{{cvar.code|safe}}{% endif %}
            {% elif forloop.last %}
              else {% if cvar.type == "calc" %}{{cvar.fname}}($search {% if cvar.dvarnum > 0 %},{% endif %} {{cvar.dvars}}){% else %}{{cvar.code|safe}}{% endif %}
            {% else %}
              else if ($searchgroup = '{{cvar.grp}}') then {% if cvar.type == "calc" %}{{cvar.fname}}($search {% if cvar.dvarnum > 0 %},{% endif %} {{cvar.dvars}}){% else %}{{cvar.code|safe}}{% endif %}
            {% endif %}
          {% endfor %}
      {% endfor %}
    
    (: Divide the results over the search group :)
    let $cat := $searchgroup
    
    (: Calculate the features :)
    let $dbList := tb:getFtList($search, $searchgroup
      {% for item in dvar_list %}
         , ${{item.name}}
      {% endfor %})
    
    (: Conditions that must hold :)
    where (
      {% for cond in cond_list %}
        {% if not forloop.first %}and {% endif %} ({{cond|safe}})
      {% endfor %}
    )
    
    (: Return the results :)
    return ru:back($search, $dbList, $cat)
  }
</TEI>