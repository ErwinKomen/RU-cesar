var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

var ru = (function ($, ru) {
  "use strict";

  ru.cesar.seeker = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_divErr = "research_err",
        oSyncTimer = null;


    // Private methods specification
    var private_methods = {
      /**
       * methodNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      methodNotVisibleFromOutside: function () {
        return "something";
      },
      errMsg: function (sMsg, ex) {
        var sHtml = "";
        if (ex === undefined) {
          sHtml = "Error: " + sMsg;
        } else {
          sHtml = "Error in [" + sMsg + "]<br>" + ex.message;
        }
        $("#" + loc_divErr).html(sHtml);
      },
      errClear: function () {
        $("#" + loc_divErr).html("");
      }
    }

    // Public methods
    return {
      /**
       * research_wizard
       *    Select one item from the research project wizard
       *
       */
      research_wizard: function(el, sPart) {
        var sTargetId = "research_container_",
            sTargetType = "",
            sObjectId = "",
            html = "",
            elListItem = null,
            elList = null;

        try {
          // Get the correct target id
          sTargetId = "#" + sTargetId + sPart;
          sObjectId = $("#researchid").text().trim();
          sTargetType = $("#id_research-targetType").val();
          // Before continuing: has the targettype been chosen?
          if (sPart !== "1") {
            // Sanity check          
            switch (sTargetType) {
              case "w":
              case "c":
                private_methods.errClear();
                break;
              default:
                // There really is no other option, so warn the user and do not change place
                private_methods.errMsg("Choose the main element type");
                // We need to LEAVE at this point
                return;
            }
          }
          // Some of these need to be loaded through an ajax call
          switch (sPart) {
            case "1":
            case "2":
            case "3":
            case "4":
            case "42":
              // CHeck if we need to take another instance id instead of #researchid
              if ($(el).attr("instanceid") !== undefined) { sObjectId = $(el).attr("instanceid");}
              // Fetch the corr
              var response = ru.cesar.seeker.ajaxform_load($(el).attr("targeturl"), sObjectId);
              if (response.status && response.status === "ok") {
                // Make the HTML response visible
                $(sTargetId).html(response.html);
                // Make sure events are set again
                ru.cesar.seeker.init_events();
              }
              break;
          }
          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").click(ru.cesar.seeker.ajaxform_click);

          // Some actions depend on the particular page we are going to visit
          switch (sPart) {
            case "4": // Page 4=Calculation
            case "42":
              // Specify the function to be called when the user presses [Calculation...]
              $(".cvar-calculate").click(ru.cesar.seeker.cvarcalculate_click);
              // Specify the function to be called when the user presses [Calculation...]
              $(".cvar-specify").click(ru.cesar.seeker.cvarspecify_click);
              // Make sure the 'Type' field values are processed everywhere
              $(".cvar-item").each(function () {
                // Perform the same function as if we were clicking it
                ru.cesar.seeker.cvartype_click(this);
              });
              // Specify the change reaction function
              $(".cvar-type select").change(ru.cesar.seeker.cvartype_click);
              // Specify the function to be called when the user presses "summary"
              $(".cvar-summary").click(ru.cesar.seeker.cvarsummary_click);
              break;
            case "5": // Page 4=Calculation
              // Make sure the 'Type' field values are processed everywhere
              $(".cvar-item").each(function () {
                // Perform the same function as if we were clicking it
                ru.cesar.seeker.cvartype_click(this);
              });
              // Specify the change reaction function
              $(".cvar-type select").change(ru.cesar.seeker.cvartype_click);
              // Specify the function to be called when the user presses "summary"
              $(".cvar-summary").click(ru.cesar.seeker.cvarsummary_click);
              break;
          }
          // Hide all research parts
          $(".research-part").not(sTargetId).addClass("hidden");
          $(".research-part").not(sTargetId).removeClass("active");

          $(sTargetId).removeClass("hidden");
          // If this is not [Project Type] then get the project type
          if (sPart !== '1') {
            // Set the <input> element
            $("#research_part").val(sTargetType);
            // Hide all 
            $(".research-wrd").addClass("hidden");
            $(".research-cns").addClass("hidden");
            // Make sure everything of this target type is unhidden
            switch (sTargetType) {
              case "w": $(".research-wrd").removeClass("hidden"); break;
              case "c": $(".research-cns").removeClass("hidden"); break;
            }
          }
          // Determine what type we are
          // And then switch to the correct page
          switch ($(el).prop("tagName").toLowerCase()) {
            case "a":
              // Get the <li> element
              elListItem = $(el).parent();
              // Get the <ul> element
              elList = $(elListItem).parent();
              // Remove all actives
              $(elList).children("li.active").removeClass("active");
              $(elListItem).addClass("active");
              break;
            case "button":
              // Get the parent of the buttons
              elList = $(el).parent();
              // Adapt all the btn classes
              $(elList).children('button').each(function() {
                if ($(this).is(el)) {
                  $(this).addClass("btn-secondary");
                  $(this).removeClass("btn-primary");
                } else {
                  $(this).removeClass("btn-secondary");
                  $(this).addClass("btn-primary");
                }
              });
              break;
          }
        } catch (ex) {
          private_methods.errMsg("research_wizard", ex);
        }
      },

      /**
       * cvartype_click
       *   Set the type of construction variable: fixed value or calculate
       *
       *   Assumptions:
       *    0 = fixed value
       *    1 = expression (function)
       *    2 = global variable
       *
       */
      cvartype_click: function (el) {
        var elRow = (el.target === undefined) ? el : $(this).closest("tr") ;
        var elType = $(elRow).find(".cvar-type").first();
        var elVal = $(elRow).find(".cvar-val-exp").first();
        // Find the type element
        var elCvarType = $(elType).find("select").first();
        // Get its value
        var elCvarTypeVal = $(elCvarType).val();
        // Hide/show, depending on the value
        switch (elCvarTypeVal) {
          case "0": // Fixed value
            $(elVal).find(".cvar-value").removeClass("hidden");
            $(elVal).find(".cvar-expression").addClass("hidden");
            $(elVal).find(".cvar-gvar").addClass("hidden");
            break;
          case "1": // Expression
            $(elVal).find(".cvar-value").addClass("hidden");
            $(elVal).find(".cvar-expression").removeClass("hidden");
            $(elVal).find(".cvar-gvar").addClass("hidden");
            break;
          case "2": // Global variable
            $(elVal).find(".cvar-value").addClass("hidden");
            $(elVal).find(".cvar-expression").addClass("hidden");
            $(elVal).find(".cvar-gvar").removeClass("hidden");
            break;
        }
      },

      /**
       * cvarsummary_click
       *   Show or hide the summary of the expression here
       *
       */
      cvarsummary_click: function () {
        // Get to the row from here
        var elRow = $(this).closest("tr");
        // Find the expression summary
        var elSum = $(elRow).find(".cvar-expression-summary");
        // Is it closed or opened?
        if ($(elSum).hasClass("hidden")) {
          // Calculate and show the value
          $(elSum).html("hier komt de waarde");
          // Unhide it
          $(elSum).removeClass("hidden");
        } else {
          // Hide it
          $(elSum).addClass("hidden");
        }
      },

      /**
       * cvarcalculate_click
       *   Show or hide the calculation of one data-specific variable for all search-elements
       *
       */
      cvarcalculate_click: function () {
        // Get the loopid 
        var loopid = $(this).attr("loopid");
        // Find the correct row
        var elCalcRow = $(this).closest("tbody").find("#" + loopid);
        // Is it closed or opened?
        if ($(elCalcRow).hasClass("hidden")) {
          // Unhide it
          $(elCalcRow).removeClass("hidden");
        } else {
          // Hide it
          $(elCalcRow).addClass("hidden");
        }
      },
      nowTime: function() {
        var now = new Date(Date.now());
        var sNow = now.getHours() + ":" + now.getMinutes() + ":" + now.getSeconds();
        return sNow;
      },

      /**
       * ajaxform_load
       *   General way to load an ajax form for 'New' or 'Edit' purposes
       *
       */
      ajaxform_load: function (ajaxurl, instanceid) {
        var data = [],      // Array to store the POST data
            response = {},
            html = "";      // The HTML code to be put

        // Initial response
        response['status'] = "none";
        // Store the instanceid
        // data.push({ 'name': 'object_id', 'value': instanceid });
        // NOTE: the form data will be fetched in the Python Server part
        // Make an AJAX GET call to get the correct HTML code
        $.ajax({
          url: ajaxurl,
          type: "GET",
          data: data,
          async: false,
          dataType: 'json',
          success: function (data) {
            // Take over the JSON response (consisting of 'status' and 'html')
            response = data;
            // Make sure events are set again
            ru.cesar.seeker.init_events();
            var x = 1;
          },
          failure: function () {
            response['status'] = "error";
            response['html'] = "AJAX get failure";
          }
        });
        // REturn the response
        return response;
      },

      /**
       * ajaxform_click
       *   General way to process an ajax form request
       *
       */
      ajaxform_click: function () {
        var data = [],      // Array to stor the POST data
            elCall = this,
            callType = "";  // Type of element that calls us

        // /WHo is calling?
        callType = $(this)[0].tagName.toLowerCase();

        // obligatory parameter: ajaxurl
        var ajaxurl = $(this).attr("ajaxurl");
        var instanceid = $(this).attr("instanceid");

        // Derive the data
        if ($(this).attr("data")) {
          data = $(this).attr("data");
        } else {
          var frm = $(this).closest("form");
          if (frm !== undefined) {
            data = $(frm).serializeArray();
          }
        }
        data.push({ 'name': 'instanceid', 'value': instanceid });
        // THird parameter: the id of the element to be opened: OPTIONAL
        var openid = $(this).attr("openid");
        // Find the element to be opened/closed
        var elOpen = null;
        if (openid !== undefined) {
          elOpen = $(this).closest("#" + openid);
        }
        // Make an AJAX call to get an existing or new specification element HTML code
        $.ajax({
          url: ajaxurl,
          type: "POST",
          data: data,
          async: false,
          dataType: 'json',
          success: function (data) {
            if (data.status && data.status === 'ok') {
              $(elOpen).html(data.html);
            }
            // Make sure events are set again
            ru.cesar.seeker.init_events();
          },
          failure: function () {
            var iStop = 1;
          }
        });
        // Bind the click event to all class="ajaxform" elements
        $(".ajaxform").click(ru.cesar.seeker.ajaxform_click);
      },

      /**
       * cvarspecify_click
       *   Create a calculation form and show it to the user
       *
       */
      cvarspecify_click: function () {
        // Get the loopid to find out exactly where we are...
        var loopid = $(this).attr("loopid");
        var vardefid = $(this).attr("vardefid");
        var constructionid = $(this).attr("constructionid");
        // Find the correct row
        var elCalcRow = $(this).closest("tbody").find("#" + loopid);
        // Is it closed or opened?
        if ($(elCalcRow).hasClass("hidden")) {
          // Find the nearest [cvar-item]
          var elCvarItem = $(this).closest("tr").find(" td.hidden div input");
          // Get the id attribute
          var cvarId = $(elCvarItem).attr("id");
          // Make an AJAX call to get an existing or new specification element HTML code
          $.ajax({
            url: '/ajax/getspecel/',
            data: {
              'cvarid': cvarId, 'vardefid': vardefid, 'constructionid': constructionid
            },
            dataType: 'json',
            success: function (data) {
              if (data.status && data.status === 'ok') {
                $(elCalcRow).html(data.specelform);
                // Unhide it
                $(elCalcRow).removeClass("hidden");
              }
            },
            failure: function () {
              var iStop = 1;
            }
          });
        } else {
          // Hide it
          $(elCalcRow).addClass("hidden");
        }
      },

      /**
       * sent_click
       *   Show waiting symbol when sentence is clicked
       *
       */
      sent_click: function () {
        $("#sentence-fetch").removeClass("hidden");
      },

      toggle_textarea_click: function() {
        var elGroup = null,
            elSpan = null,
            sStatus = "";

        // Get the following <span> of class td-textarea
        elSpan = $(this).next(".td-textarea");
        // Sanity check
        if (elSpan !== null) {
          // Show it if needed
          if ($(elSpan).hasClass("hidden")) {
            $(elSpan).removeClass("hidden");
          }
          // Hide myself
          $(this).addClass("hidden");
        }
      },

      toggle_textarea_out: function() {
        var elSpan = null,
            sText = "";

        // Get the text inside the textarea
        sText = $(this).children().first().html();
        if ($.trim(sText) !== "") {
          // Get the previous <span> of class td-toggle-textarea
          elSpan = $(this).prev(".td-toggle-textarea");
          // Check
          if (elSpan !== null) {
            // Hide the textarea and show the text
            $(elSpan).children().first().html(sText);
            $(elSpan).removeClass("hidden");
            $(this).addClass("hidden");
          }
        }
      },

      /**
       * tabular_addrow
       *   Add one row into a tabular inline
       *
       */
      tabular_addrow: function () {
        var arTable = ['research_intro-wrd', 'research_intro-cns', 'research_gvar', 'research_vardef', 'research_spec'],
            arPrefix = ['construction', 'construction', 'gvar', 'vardef', 'function'],
            arNumber = [true, true, false, false, false],
            elTable = null,
            iNum = 0,     // Number of <tr class=form-row> (excluding the empty form)
            sId = "",
            i;

        // Find out just where we are
        sId = $(this).closest("div").attr("id");
        // Walk all tables
        for (i = 0; i < arTable.length; i++) {
          if (sId === arTable[i] || sId.indexOf(arTable[i]) >=0) {
            // Go to the <tbody> and find the last form-row
            elTable = $(this).closest("tbody").children("tr.form-row.empty-form")

            // Perform the cloneMore function to this <tr>
            ru.cesar.seeker.cloneMore(elTable, arPrefix[i], arNumber[i]);
            // We are done...
            break;
          }
        }
      },

      /**
       *  cloneMore
       *      Add a form to the formset
       *      selector = the element that should be duplicated
       *      type     = the formset type
       *      number   = boolean indicating that re-numbering on the first <td> must be done
       *
       */
      cloneMore: function (selector, type, number) {
        try {
          // Clone the element in [selector]
          var newElement = $(selector).clone(true);
          // Find the total number of [type] elements
          var total = $('#id_' + type + '-TOTAL_FORMS').val();

          // Find each <input> element
          newElement.find(':input').each(function () {
            // Get the name of this element, adapting it on the fly
            var name = $(this).attr("name").replace("__prefix__", total.toString());
            // Produce a new id for this element
            var id = $(this).attr("id").replace("__prefix__", total.toString());
            // Adapt this element's name and id, unchecking it
            $(this).attr({ 'name': name, 'id': id }).val('').removeAttr('checked');
          });
          newElement.find('select').each(function () {
            // Get the name of this element, adapting it on the fly
            var name = $(this).attr("name").replace("__prefix__", total.toString());
            // Produce a new id for this element
            var id = $(this).attr("id").replace("__prefix__", total.toString());
            // Adapt this element's name and id, unchecking it
            $(this).attr({ 'name': name, 'id': id }).val('').removeAttr('checked');
          });

          // Find each <label> under newElement
          newElement.find('label').each(function () {
            // Adapt the 'for' attribute
            var newFor = $(this).attr("for").replace("__prefix__", total.toString());
            $(this).attr('for', newFor);
          });
          
          // Look at the inner text of <td>
          newElement.find('td').each(function () {
            var elText = $(this).children().first();
            if (elText !== undefined) {
              $(elText).text($(elText).text().replace("__counter__", total.toString()));
            }
          });
          // Look at the attributes of <a>
          newElement.find('a').each(function () {
            // Iterate over all attributes
            var elA = this;
            $.each(elA.attributes, function (i, attrib) {
              var attrText = $(elA).attr(attrib.name).replace("__counter__", total.toString());
              $(this).attr(attrib.name, attrText);
            });
          });


          // Adapt the total number of forms in this formset
          total++;
          $('#id_' + type + '-TOTAL_FORMS').val(total);

          // Adaptations on the new <tr> itself
          newElement.attr("id", "arguments-"+(total-1).toString());
          newElement.attr("class", "form-row row" + total.toString());

          // Insert the new element before the selector = empty-form
          $(selector).before(newElement);

          // Should we re-number?
          if (number !== undefined && number) {
            // Walk all <tr> elements of the table
            var iRow = 1;
            $(selector).closest("tbody").children("tr.form-row").not(".empty-form").each(function () {
              var elFirstCell = $(this).find("td").not(".hidden").first();
              $(elFirstCell).html(iRow);
              iRow += 1;
            });
          }

        } catch (ex) {
          private_methods.errMsg("cloneMore", ex);
        }
      },


      /**
       *  part_detail_toggle
       *      Toggle part detail
       *
       */
      part_detail_toggle: function (iPk) {
        var sId = "";

        // validate
        if (iPk === undefined) return;
        // Get the name of the tag
        sId = "#part_details_" + iPk.toString();
        // Check if it is visible or not
        if ($(sId).hasClass("hidden")) {
          // Remove it
          $(sId).removeClass("hidden");
        } else {
          // Add it
          $(sId).addClass("hidden");
        }
      },

      init_events: function () {
        $('tr.add-row a').click(ru.cesar.seeker.tabular_addrow);
        $('.inline-group > div > a.btn').click(function () {
          var elGroup = null,
              elTabular = null,
              sStatus = "";

          // Get the tabular
          elTabular = $(this).parent().next(".tabular");
          if (elTabular !== null) {
            // Get the status of this one
            if ($(elTabular).hasClass("hidden")) {
              $(elTabular).removeClass("hidden");
            } else {
              $(elTabular).addClass("hidden");
            }
          }
        });
        $('td span.td-toggle-textarea').click(ru.cesar.seeker.toggle_textarea_click);
        $('td span.td-textarea').mouseout(ru.cesar.seeker.toggle_textarea_out);
      }


    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

