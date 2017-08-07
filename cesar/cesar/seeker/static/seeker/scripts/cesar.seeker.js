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
            sMsg = "",
            html = "",
            data = {},
            frm = null,
            response = null,
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
          // Find the currently shown 'research-part' form
          frm = $(".research-part").not(".hidden").find("form");
          // [1] Some (increasingly many) calls require FIRST saving of the currently loaded information
          switch (sPart) {
            case "42": sMsg = "4-before-42";
            case "43": sMsg = "42-before-43";
            case "44": sMsg = "43-before-44";
              // Opening a new form requires prior processing of the current form
              if (frm !== undefined) {
                data = $(frm).serializeArray();
                var button = $(frm).find(".submit-row .ajaxform");
                if (button !== undefined) {
                  // Indicate we are saving
                  $(".save-warning").html("Processing... "+sMsg);
                  data.push({ 'name': 'instanceid', 'value': $(button).attr("instanceid") });
                  // Process this information: save the data!
                  response = ru.cesar.seeker.ajaxcall($(button).attr("ajaxurl"), data, "POST");
                  // Check the response
                  if (response.status === undefined || response.status !== "ok") {
                    // Action to undertake if we have not been successfull
                    private_methods.errMsg("research_wizard["+sPart+"]: could not save the data for this function");
                  }
                }
              }
              break;
          }

          // [2] Load the new form through an AJAX call
          switch (sPart) {
            case "1":
            case "2":
            case "3":
            case "4":
            case "42":
            case "43":
            case "44":
              // CHeck if we need to take another instance id instead of #researchid
              if ($(el).attr("instanceid") !== undefined) { sObjectId = $(el).attr("instanceid"); }
              // Indicate we are saving/preparing
              $(".save-warning").html("Processing... " + sPart);
              // Fetch the corr
              response = ru.cesar.seeker.ajaxform_load($(el).attr("targeturl"), sObjectId);
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
              // add any event handlers for wizard part '42'
              ru.cesar.seeker.init_cvar_events();
              break;
            case "43":
            case "44":
              // add any event handlers for wizard part '43' and part '44'
              ru.cesar.seeker.init_arg_events();
              break;
            case "5": // Page 5=Conditions

              // TODO: this still needs to be specified

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
       * argtype_click
       *   Set the type of argument: fixed value, select or  calculate
       *
       *   Assumptions:
       *    0 = fixed value
       *    1 = global variable
       *    2 = construction variable
       *    3 = expression (function)
       *
       */
      argtype_click: function (el) {
        try {
          var elRow = (el.target === undefined) ? el : $(this).closest("tr");
          var elType = $(elRow).find(".arg-type").first();
          var elVal = $(elRow).find(".arg-val-exp").first();
          // Find the type element
          var elArgType = $(elType).find("select").first();
          // Get its value
          var elArgTypeVal = $(elArgType).val();
          // Hide/show, depending on the value
          switch (elArgTypeVal) {
            case "fixed": // Fixed value
              $(elVal).find(".arg-value").removeClass("hidden");
              $(elVal).find(".arg-expression").addClass("hidden");
              $(elVal).find(".arg-gvar").addClass("hidden");
              $(elVal).find(".arg-cvar").addClass("hidden");
              $(elVal).find(".arg-cnst").addClass("hidden");
              $(elVal).find(".arg-axis").addClass("hidden");
              break;
            case "gvar": // Global variable
              $(elVal).find(".arg-value").addClass("hidden");
              $(elVal).find(".arg-expression").addClass("hidden");
              $(elVal).find(".arg-gvar").removeClass("hidden");
              $(elVal).find(".arg-cvar").addClass("hidden");
              $(elVal).find(".arg-cnst").addClass("hidden");
              $(elVal).find(".arg-axis").addClass("hidden");
              break;
            case "cvar": // Constructuion variable
              $(elVal).find(".arg-value").addClass("hidden");
              $(elVal).find(".arg-expression").addClass("hidden");
              $(elVal).find(".arg-gvar").addClass("hidden");
              $(elVal).find(".arg-cvar").removeClass("hidden");
              $(elVal).find(".arg-cnst").addClass("hidden");
              $(elVal).find(".arg-axis").addClass("hidden");
              break;
            case "func": // Expression
              $(elVal).find(".arg-value").addClass("hidden");
              $(elVal).find(".arg-expression").removeClass("hidden");
              $(elVal).find(".arg-gvar").addClass("hidden");
              $(elVal).find(".arg-cvar").addClass("hidden");
              $(elVal).find(".arg-cnst").addClass("hidden");
              $(elVal).find(".arg-axis").addClass("hidden");
              break;
            case "cnst":  // Constituent
              $(elVal).find(".arg-value").addClass("hidden");
              $(elVal).find(".arg-expression").addClass("hidden");
              $(elVal).find(".arg-gvar").addClass("hidden");
              $(elVal).find(".arg-cvar").addClass("hidden");
              $(elVal).find(".arg-cnst").removeClass("hidden");
              $(elVal).find(".arg-axis").addClass("hidden");
              break;
            case "axis":  // Axis
              $(elVal).find(".arg-value").addClass("hidden");
              $(elVal).find(".arg-expression").addClass("hidden");
              $(elVal).find(".arg-gvar").addClass("hidden");
              $(elVal).find(".arg-cvar").addClass("hidden");
              $(elVal).find(".arg-cnst").addClass("hidden");
              $(elVal).find(".arg-axis").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("argtyp_click", ex);
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
        try {
          var elRow = (el.target === undefined) ? el : $(this).closest("tr");
          var elType = $(elRow).find(".cvar-type").first();
          var elVal = $(elRow).find(".cvar-val-exp").first();
          // Find the type element
          var elCvarType = $(elType).find("select").first();
          // Get its value
          var elCvarTypeVal = $(elCvarType).val();
          // Hide/show, depending on the value
          switch (elCvarTypeVal) {
            case "fixed": // Fixed value
              $(elVal).find(".cvar-value").removeClass("hidden");
              $(elVal).find(".cvar-expression").addClass("hidden");
              $(elVal).find(".cvar-gvar").addClass("hidden");
              break;
            case "calc": // Expression
              $(elVal).find(".cvar-value").addClass("hidden");
              $(elVal).find(".cvar-expression").removeClass("hidden");
              $(elVal).find(".cvar-gvar").addClass("hidden");
              break;
            case "gvar": // Global variable
              $(elVal).find(".cvar-value").addClass("hidden");
              $(elVal).find(".cvar-expression").addClass("hidden");
              $(elVal).find(".cvar-gvar").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("cvartype_click", ex);
        }
      },

      /**
       * cvarsummary_click
       *   Show or hide the summary of the expression here
       *
       */
      cvarsummary_click: function () {
        try {
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
        } catch (ex) {
          private_methods.errMsg("cvarsummary_click", ex);
        }
      },

      /**
       * cvarcalculate_click
       *   Show or hide the calculation of one data-specific variable for all search-elements
       *
       */
      cvarcalculate_click: function () {
        try {
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
        } catch (ex) {
          private_methods.errMsg("cvarcalculate_click", ex);
        }
      },

      /**
       * nowTime
       *   Get the current time as a string
       *
       */
      nowTime: function () {
        var now = new Date(Date.now());
        var sNow = now.getHours() + ":" + now.getMinutes() + ":" + now.getSeconds();
        return sNow;
      },

      /**
       * ajaxform_load
       *   General way to load an ajax form for 'New' or 'Edit' purposes
       *
       */
      ajaxform_load: function (ajaxurl, instanceid, data) {
        var response = {},
            html = "";      // The HTML code to be put

        try {
          // Initial response
          response['status'] = "none";
          // See if data needs to be initialized
          if (data === undefined) {
            data = [];      // Array to store the POST data
          }
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
        } catch (ex) {
          private_methods.errMsg("ajaxform_load", ex);
          return {'status': 'error', 'html': ex.message};
        }
      },

      /**
       * ajaxcall
       *   Make an AJAX call to the URL with the data
       *   Use the method specified: POST or GET
       *
       */
      ajaxcall: function (sUrl, data, sMethod) {
        var response = {};

        try {
          if (sUrl === undefined || sUrl === "" || data === undefined) {
            // Cannot do anything with this, so respond with a bad status
            response['status'] = "error";
            response['msg'] = "Missing obligatory parameter(s): URL, data";
            return response;
          }
          // There is valid information, continue
          $.ajax({
            url: sUrl,
            type: sMethod,
            data: data,
            async: false,
            dataType: 'json',
            success: function (data) {
              response = data;
            },
            failure: function () {
              var iStop = 1;
            }
          });
          // Return the response
          return response;
        } catch (ex) {
          private_methods.errMsg("ajaxcall", ex);
        }
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

        try {
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
          // Indicate we are saving/preparing
          $(".save-warning").html("Saving item... " + instanceid.toString());
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
              switch (openid) {
                case "research_container_42":
                  // add any event handlers for wizard part '42'
                  ru.cesar.seeker.init_cvar_events();
                  break;
                case "research_container_43":
                case "research_container_44":
                  // add any event handlers for wizard part '43' and '44'
                  ru.cesar.seeker.init_arg_events();
                  break;
              }
            },
            failure: function () {
              var iStop = 1;
            }
          });
          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").click(ru.cesar.seeker.ajaxform_click);
        } catch (ex) {
          private_methods.errMsg("ajaxform_click", ex);
        }
      },

      /**
       * cvarspecify_click
       *   Create a calculation form and show it to the user
       *
       */
      cvarspecify_click: function () {
        try {
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
        } catch (ex) {
          private_methods.errMsg("cvarspecify_click", ex);
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

      /**
       * toggle_textarea_click
       *   Action when user clicks [textarea] element
       *
       */
      toggle_textarea_click: function () {
        var elGroup = null,
            elSpan = null,
            sStatus = "";

        try {
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
        } catch (ex) {
          private_methods.errMsg("toggle_textarea_click", ex);
        }
      },

      /**
       * toggle_textarea_out
       *   Action when mouse leaves [textarea] element
       *
       */
      toggle_textarea_out: function () {
        var elSpan = null,
            sText = "";

        try {
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
        } catch (ex) {
          private_methods.errMsg("toggle_textarea_out", ex);
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

        try {
          // Find out just where we are
          sId = $(this).closest("div").attr("id");
          // Walk all tables
          for (i = 0; i < arTable.length; i++) {
            if (sId === arTable[i] || sId.indexOf(arTable[i]) >= 0) {
              // Go to the <tbody> and find the last form-row
              elTable = $(this).closest("tbody").children("tr.form-row.empty-form")

              // Perform the cloneMore function to this <tr>
              ru.cesar.seeker.cloneMore(elTable, arPrefix[i], arNumber[i]);
              // We are done...
              break;
            }
          }
        } catch (ex) {
          private_methods.errMsg("tabular_addrow", ex);
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

        try {
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
        } catch (ex) {
          private_methods.errMsg("part_detail_toggle", ex);
        }
      },

      /**
       *  init_cvar_events
       *      Bind events to work with constituent variables
       *
       */
      init_cvar_events: function () {
        try {
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
          // When the function-definition-selection changes, the button name should change
          $(".cvar-fundef select").change(function () {
            var button = $(this).closest(".cvar-expression").find("a.btn").first();
            if (button !== null) {
              $(button).html("create");
            }
          });
        } catch (ex) {
          private_methods.errMsg("init_cvar_events", ex);
        }
      },

      /**
       *  init_arg_events
       *      Bind events to work with function arguments
       *
       */
      init_arg_events: function () {
        try {
          // Make sure the 'Type' field values are processed everywhere
          $(".arg-item").each(function () {
            // Perform the same function as if we were clicking it
            ru.cesar.seeker.argtype_click(this);
          });
          // Specify the change reaction function
          $(".arg-type select").change(ru.cesar.seeker.argtype_click);
        } catch (ex) {
          private_methods.errMsg("init_arg_events", ex);
        }
      },

      /**
       *  init_events
       *      Bind main necessary events
       *
       */
      init_events: function () {
        try {
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
          // NOTE: do not use the following mouseout event--it is too weird to work with
          // $('td span.td-textarea').mouseout(ru.cesar.seeker.toggle_textarea_out);
        } catch (ex) {
          private_methods.errMsg("init_events", ex);
        }
      }


    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

