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
        oSyncTimer = null,
        loc_sWaiting = " <span class=\"glyphicon glyphicon-refresh glyphicon-refresh-animate\"></span>",
        basket_progress = "",         // URL to get progress
        basket_stop = "",             // URL to stop the basket
        basket_result = "",           // URL to the results for this basket
        basket_data = null,           // DATA to be sent along
        lAddTableRow = [
          { "table": "research_intro-wrd", "prefix": "construction", "counter": true, "events": null},
          { "table": "research_intro-cns", "prefix": "construction", "counter": true, "events": null },
          { "table": "research_shareg", "prefix": "shareg", "counter": false, "events": null },
          { "table": "research_gvar", "prefix": "gvar", "counter": false, "events": null },
          { "table": "research_vardef", "prefix": "vardef", "counter": false, "events": null },
          { "table": "research_spec", "prefix": "function", "counter": false, "events": null },
          { "table": "research_cond", "prefix": "cond", "counter": true, "events": function () { ru.cesar.seeker.init_cond_events(); } },
          { "table": "result_kwicfilter", "prefix": "filter", "counter": true, "events": null },
      ];


    // Private methods specification
    var private_methods = {
      /**
       * methodNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      methodNotVisibleFromOutside: function () {
        return "something";
      },
      /**
       *  var_move
       *      Move variable row one step down or up
       *      This means the 'order' attribute changes
       */
      var_move: function (el, sDirection) {
        var elRow = null,
            rowSet = null,
            iLen = 0;

        try {
          // Find the current row
          elRow = $(el).closest("tr");
          switch (sDirection) {
            case "down":
              // Put the 'other' (=next) row before me
              $(elRow).next().after($(elRow));
              break;
            case "up":
              // Put the 'other' (=next) row before me
              $(elRow).prev().before($(elRow));
              break;
            default:
              return;
          }
          // Now iterate over all rows in this table
          rowSet = $(elRow).parent().children(".form-row").not(".empty-form");
          iLen = $(rowSet).length;
          $(rowSet).each(function (index, el) {
            var elInput = $(el).find(".var-order input");
            var sOrder = $(elInput).val();
            // Set the order of this element
            if (parseInt(sOrder, 10) !== index + 1) {
              $(elInput).attr("value", index + 1);
              $(elInput).val(index + 1);
            }
            // Check visibility of up and down
            $(el).find(".var-down").removeClass("hidden");
            $(el).find(".var-up").removeClass("hidden");
            if (index === 0) {
              $(el).find(".var-up").addClass("hidden");
            }
            if (index === iLen - 1) {
              $(el).find(".var-down").addClass("hidden");
            }
          });
        } catch (ex) {
          private_methods.errMsg("var_move", ex);
        }
      },
      errMsg: function (sMsg, ex) {
        var sHtml = "";
        if (ex === undefined) {
          sHtml = "Error: " + sMsg;
        } else {
          sHtml = "Error in [" + sMsg + "]<br>" + ex.message;
        }
        sHtml = "<code>" + sHtml + "</code>";
        $("#" + loc_divErr).html(sHtml);
      },
      errClear: function () {
        $("#" + loc_divErr).html("");
      },
      waitInit: function (el) {
        var elResPart = null,
            elWait = null;

        try {
          // Set waiting div
          elResPart = $(el).closest(".research_part");
          if (elResPart !== null) {
            elWait = $(elResPart).find(".research-fetch").first();
          }
          return elWait;
        } catch (ex) {
          private_methods.errMsg("waitInit", ex);
        }
      },
      waitStart: function(el) {
        if (el !== null) {
          $(el).removeClass("hidden");
        }
      },
      waitStop: function (el) {
        if (el !== null) {
          $(el).addClass("hidden");
        }
      }
    }

    // Public methods
    return {
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
          $(elVal).find(".arg-value").addClass("hidden");
          $(elVal).find(".arg-expression").addClass("hidden");
          $(elVal).find(".arg-gvar").addClass("hidden");
          $(elVal).find(".arg-cvar").addClass("hidden");
          $(elVal).find(".arg-dvar").addClass("hidden");
          $(elVal).find(".arg-cnst").addClass("hidden");
          $(elVal).find(".arg-search").addClass("hidden");
          $(elVal).find(".arg-axis").addClass("hidden");
          switch (elArgTypeVal) {
            case "fixed": // Fixed value
              $(elVal).find(".arg-value").removeClass("hidden");
              break;
            case "gvar": // Global variable
              $(elVal).find(".arg-gvar").removeClass("hidden");
              break;
            case "cvar": // Constructuion variable
              $(elVal).find(".arg-cvar").removeClass("hidden");
              break;
            case "dvar": // Data-dependant variable
              $(elVal).find(".arg-dvar").removeClass("hidden");
              break;
            case "func": // Expression
              $(elVal).find(".arg-expression").removeClass("hidden");
              break;
            case "cnst":  // Constituent
              $(elVal).find(".arg-cnst").removeClass("hidden");
              break;
            case "axis":  // Axis
              $(elVal).find(".arg-axis").removeClass("hidden");
              break;
            case "hit":  // Search hit
              $(elVal).find(".arg-search").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("argtyp_click", ex);
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
       *   General way to process an ajax form request:
       *   1 - Issue a POST request to send (and save) data
       *   2 - Issue a GET request to receive updated data
       *
       */
      ajaxform_click: function () {
        var data = [],      // Array to store the POST data
            elCall = this,
            response = null,
            elWait = null,
            callType = "";  // Type of element that calls us

        try {
          // Set waiting div
          elWait = private_methods.waitInit(this);
          // Start waiting
          private_methods.waitStart(elWait);
          // /WHo is calling?
          callType = $(this)[0].tagName.toLowerCase();

          // obligatory parameter: ajaxurl
          var ajaxurl = $(this).attr("ajaxurl");
          var instanceid = $(this).attr("instanceid");
          var bNew = (instanceid.toString() === "None");

          // Derive the data
          if ($(this).attr("data")) {
            data = $(this).attr("data");
            if (data !== "") {
              data = JSON.parse(data);
            }
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
          if (!bNew) {
            $(".save-warning").html("Saving item... " + instanceid.toString());
          }
          // Make an AJAX call to get an existing or new specification element HTML code
          response = ru.cesar.seeker.ajaxcall(ajaxurl, data, "POST");
          if (response.status === undefined || response.status !== 'ok') {
            // Show an error somewhere

          } else if (bNew && 'instanceid' in response) {
            // A new item has been created, and now we receive its 'instanceid'
            instanceid = response['instanceid'];
            // Add the instanceid to the URL, so that the new item gets opened
            ajaxurl = ajaxurl + instanceid + "/";
            // Also find the 'goto_overview' and adpat its @targeturl property
            var elOview = $("#goto_overview").children("button").first();
            if (elOview !== undefined && elOview !== null) {
              var sOviewUrl = $(elOview).attr("targeturl");
              sOviewUrl = sOviewUrl.replace("/new/", "/" + instanceid + "/");
              $(elOview).attr("targeturl", sOviewUrl);
            }
          }
          // Check whether we need to show the error response
          if ('has_errors' in response) {
            // Yes, show the resulting form with the errors
            $(elOpen).html(response.html);
            // Make sure events are set again
            ru.cesar.seeker.init_events();
            // Bind the click event to all class="ajaxform" elements
            $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);
            // Stop waiting
            private_methods.waitStop(elWait);
            // And return
            return;
          }

          // Indicate we are loading
          $(".save-warning").html("Updating item... " + instanceid.toString());
          // Make a GET call with fresh data
          data = [];
          data.push({ 'name': 'instanceid', 'value': instanceid });
          // Add parameters depending on the openid
          switch (openid) {
            case "result_container_3":
              // Need to add the 'qc_select' value
              var iQcSelect = $("#qc_select").val();
              data.push({ 'name': 'qc_select', 'value': iQcSelect });
              break;
          }
          // Make an AJAX call to get an existing or new specification element HTML code
          response = ru.cesar.seeker.ajaxcall(ajaxurl, data, "GET");
          if (response !== undefined && response.status && response.status === 'ok') {
            // Load the new data
            $(elOpen).html(response.html);
            // Make sure events are set again
            ru.cesar.seeker.init_events();
            switch (openid) {
              case "research_container_42":
                // add any event handlers for wizard part '42'
                ru.cesar.seeker.init_cvar_events();
                break;
              case "research_container_43":
              case "research_container_44":
              case "research_container_62":
              case "research_container_63":
                // add any event handlers for wizard part '43' and '44' and '62'
                ru.cesar.seeker.init_arg_events();
                break;
              case "research_container_6":
                // add any event handlers for wizard part '46'
                ru.cesar.seeker.init_cond_events();
                break;
            }
          }


          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);
          // Stop waiting
          private_methods.waitStop(elWait);
        } catch (ex) {
          private_methods.errMsg("ajaxform_click", ex);
          // Stop waiting
          private_methods.waitStop(elWait);
        }
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

          // If there is an instance ID, then make sure the URL ends with that id
          if (instanceid !== undefined && instanceid !== '') {
            if (ajaxurl.indexOf('/' + instanceid + "/") < 0) {
              ajaxurl += instanceid + "/";
            }
          }

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
              var sHtml = $(elText).html();
              if (sHtml !== undefined && sHtml !== "") {
                sHtml = sHtml.replace("__counter__", total.toString());
                $(elText).html(sHtml);
              }
              // $(elText).html($(elText).html().replace("__counter__", total.toString()));
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
          newElement.attr("id", "arguments-" + (total - 1).toString());
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
       * condtype_click
       *   Set the type of condition: dvar versus func
       *
       */
      condtype_click: function (el) {
        try {
          var elRow = (el.target === undefined) ? el : $(this).closest("tr");
          var elType = $(elRow).find(".cond-type").first();
          var elVal = $(elRow).find(".cond-val-exp").first();
          // Find the type element
          var elcondtype = $(elType).find("select").first();
          // Get its value
          var elcondtypeVal = $(elcondtype).val();
          // Hide/show, depending on the value
          switch (elcondtypeVal) {
            case "dvar": // Data-dependant variable
              $(elVal).find(".cond-dvar").removeClass("hidden");
              $(elVal).find(".cond-expression").addClass("hidden");
              break;
            case "func": // Function
              $(elVal).find(".cond-dvar").addClass("hidden");
              $(elVal).find(".cond-expression").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("condtype_click", ex);
        }
      },

      /**
       * corpus_choice
       *   Process the chosen corpus-part and show the result
       *
       */
      corpus_choice : function(el, sTarget) {
        var divTarget = "",
            divOption = null, // Chosen <option>
            sLanguage = "",   // Chosen language
            sPart = "",       // Chosen corpus part
            sHtml = "",
            iChosen = 0,      // ID of chosen one
            sChosen = "";     // Option that has been chosen

        try {
          // Get the target <div>
          divTarget = "#" + sTarget;
          // Find out what has been chosen
          sChosen = $("#select_part").val();
          if (sChosen !== undefined && sChosen !== "" && sChosen !== "-") {
            // Also set the [searchPart] parameter
            $("#searchPart").attr("value", sChosen);
            // Get the integer that has been chosen
            iChosen = parseInt(sChosen, 10);
            divOption = $("#select_part").find("option[value=" + iChosen + "]");
            if (divOption !== undefined && divOption !== null) {
              sPart = $(divOption).text();
              sLanguage = $(divOption).closest("optgroup").attr("label");
              sHtml = "<div class='col-md-12'><table class='seeker-choice'><tr><td>Language: </td><td class='b'>" + sLanguage + "</td></tr>" +
                "<tr><td>Corpus (part):</td><td class='b'>" + sPart + "</td></tr></table></div>";
              $(divTarget).html(sHtml);

              // TODO: Check whether this search has already been made
            }
          }

        } catch (ex) {
          private_methods.errMsg("corpus_choice", ex);
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
       *  funcdefshow
       *      Show the function definition
       *
       */
      funcdefshow: function (el, sMyClass) {
        var elTr = null,
            sClass = "function-details";

        try {
          if (sMyClass !== undefined && sMyClass !== "") {
            sClass = sMyClass;
          }
          // Get to the nearest <tr>
          elTr = $(el).closest("tr");
          // Get to the next row
          elTr = $(elTr).nextAll("."+sClass).first();
          // Check its status
          if ($(elTr).hasClass("hidden")) {
            // Hide all other [function-details]
            $(elTr).closest("table").find("." + sClass).addClass("hidden");
            // It's hidden, so open it
            $(elTr).removeClass("hidden");
          } else {
            // It's open, so close it
            $(elTr).addClass("hidden");
          }


        } catch (ex) {
          private_methods.errMsg("funcdefshow", ex);
        }
      },

      /**
       * get_summary_click
       *   Show or hide the summary of the expression here
       *
       */
      get_summary_click: function (el, target) {
        var response,   // The ID of the current row
            sTargetId = "#cvar_summary";

        try {
          // Possibly get target
          if (target !== undefined && target !== "") {
            sTargetId = target;
          }
          // Get to the row from here
          var elRow = $(el).closest("tr");
          // Find the expression summary
          var elSum = $(sTargetId);
          // Is it closed or opened?
          if ($(elSum).hasClass("hidden")) {
            // Calculate and show the value
            response = ru.cesar.seeker.ajaxform_load($(el).attr("targeturl"));
            if (response.status && response.status === "ok") {
              // Make the HTML response visible
              $(elSum).html(response.html);
              // Make sure events are set again
              ru.cesar.seeker.init_events();
            }
            // Unhide it
            $(elSum).removeClass("hidden");
          } else {
            // Hide it
            $(elSum).addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("get_summary_click", ex);
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
       *  init_cond_events
       *      Bind events to work with conditions
       *
       */
      init_cond_events: function () {
        try {
          // Make sure the 'Type' field values are processed everywhere
          $(".cond-item").each(function () {
            // Perform the same function as if we were clicking it
            ru.cesar.seeker.condtype_click(this);
          });
          // Specify the change reaction function
          $(".cond-type select").change(ru.cesar.seeker.condtype_click);
          // Specify the function to be called when the user presses "summary"
          $(".func-summary").unbind('click');
          $(".func-summary").click(function () { ru.cesar.seeker.get_summary_click(this, "#cond_summary"); });
        } catch (ex) {
          private_methods.errMsg("init_cond_events", ex);
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
          $(".func-summary").click(function () { ru.cesar.seeker.get_summary_click(this, "#cvar_summary"); });
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
       *  click_if_new
       *      If the [divObject] is empty, then click on [sTarget]
       *
       */
      click_if_new: function (divObject, sTarget) {
        try {
          if (divObject !== undefined && sTarget !== undefined) {
            var sContent = $("#" + divObject).text().trim();
            if (sContent === "" || sContent === "None") {
              $("#" + sTarget).click();
            }
          }
        } catch (ex) {
          private_methods.errMsg("click_if_new", ex);
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
          // Make sure variable ordering is supported
          $('td span.var-down').click(ru.cesar.seeker.var_down);
          $('td span.var-up').click(ru.cesar.seeker.var_up);
          // NOTE: do not use the following mouseout event--it is too weird to work with
          // $('td span.td-textarea').mouseout(ru.cesar.seeker.toggle_textarea_out);

          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);
        } catch (ex) {
          private_methods.errMsg("init_events", ex);
        }
      },

      /**
       * kwic_page
       *    Make sure we go to the indicated page
       * 
       * @param {type} iPage
       * @param {type} sFormDiv
       */
      kwic_page: function (iPage, sFormDiv) {
        var elStart = null;

        try {
          elStart = $("#"+sFormDiv);
          ru.cesar.seeker.load_kwic(elStart, iPage);
        } catch (ex) {
          private_methods.errMsg("kwic_page", ex);
        }
      },

      /**
       * load_kwic
       *   Make an AJAX request to load data for a Kwic instance
       * 
       * @param {dom}  elStart
       * @param {int}  iPage
       */
      load_kwic: function (elStart, iPage) {
        var data = [],
            targetid = "",
            waitid = "#kwic-fetch",
            ajaxurl = "",
            frm = null,
            response = null,
            instanceid = "";

        try {
          // Clear the errors
          private_methods.errClear();

          // obligatory parameter: ajaxurl
          //ajaxurl = $(elStart).attr("ajaxurl");
          //instanceid = $(elStart).attr("instanceid");
          ajaxurl = $(elStart).attr("targeturl");
          targetid = $(elStart).attr("targetid");

          // Gather the information
          frm = $(elStart).closest("form");
          if (frm !== undefined) { data = $(frm).serializeArray(); }

          //data.push({ 'name': 'instanceid', 'value': instanceid });
          data.push({ 'name': 'target', 'value': targetid });

          if (iPage === undefined) { iPage = 1; }
          data.push({ 'name': 'page', 'value': iPage });

          // Indicate we are waiting
          $(waitid).removeClass("hidden");
          // Define the post command
          var posting = $.post(ajaxurl, data);
          // Execute the post command and tell what needs to be done when ready
          posting.done(function (data) {
            // Put the results on display
            $("#"+targetid).html(data['html']);
            // Indicate we are ready
            $(waitid).addClass("hidden");
          });

        } catch (ex) {
          private_methods.errMsg("load_kwic", ex);
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
       *  process_item
       *      Make a POST request to copy or delete an item
       *      Also show the waiting symbol by un-hiding a particular row
       *
       */
      process_item: function (el) {
        var elDiv = null,
            elNext = null,
            response = null,
            sUrl = "",
            frm = null,
            data = [];

        try {
          // Get to the nearest <div>
          elDiv = $(el).closest("div");
          // Get its second following sibling div
          elNext = $(elDiv).next(".part-process");
          if (elNext !== null) {
            //  We now have the correct row: open it
            $(elNext).removeClass("hidden");
            $(elDiv).addClass("hidden");
          }
          frm = $(el).closest("form");
          if (frm !== undefined) {
            data = $(frm).serializeArray();
            sUrl = $(el).attr("url");
            data.push({ 'name': 'caller', 'value': sUrl });
            // Anyway, start off an ajax call to request deletion
            response = ru.cesar.seeker.ajaxcall(sUrl, data, "POST");
            if (response !== undefined) {
              if (response.status === "ok") {
                // Continue through to the 'success' url
                sUrl = $(el).attr("success");
                window.location.href = sUrl;
              } else {
                // SOme kind of error was returned
                $(elNext).html(response.html);
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("process_item", ex);
        }
      },

      /**
       * research_conditions
       *   Show the 'conditions' part and hide the remainder
       *
       */
      research_finetune(el) {
        try {
          // Hide the contents and show the tiles
          $("#research_tiles").addClass("hidden");
          $("#research_contents").addClass("hidden");
          $("#goto_overview").removeClass("hidden");
          $("#goto_finetune").addClass("hidden");
          $("#research_conditions").removeClass("hidden");
        } catch (ex) {
          private_methods.errMsg("research_conditions", ex);
        }
      },

      /**
       * research_open
       *   Open up a section and close another one
       *
       */
      research_open: function (sDivName, sDivClose, sBtnOpen, sBtnClose) {
        try {
          if (sDivName !== undefined && sDivName !== '') {
            $("#" + sDivName).removeClass("hidden");
          }
          // Possibly close [sDivClose]
          if (sDivClose !== undefined && sDivClose !== "") {
            $("#" + sDivClose).addClass("hidden");
          }
          // Possible open button
          if (sBtnOpen !== undefined && sBtnOpen !== '') {
            $("#" + sBtnOpen).removeClass("hidden");
          }
          // Possibly close [sBtnClose]
          if (sBtnClose !== undefined && sBtnClose !== "") {
            $("#" + sBtnClose).addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("research_open", ex);
        }
      },

      /**
       * research_overview
       *   Show the tiles-overview
       *
       */
      research_overview(el) {
        var sTargetUrl = "";

        try {
          // Try get the target url
          sTargetUrl = $(el).attr("targeturl");
          // Open this page
          window.location.href = sTargetUrl;
        } catch (ex) {
          private_methods.errMsg("research_overview", ex);
        }
      },


      /**
       * result_wizard
       *    Select one item from the result wizard
       *
       */
      result_wizard: function (el, sPart) {
        var sTargetId = "result_container_",
            sTargetType = "",
            sObjectId = "",
            sMsg = "",
            html = "",
            sAjaxMethod = "",
            data = {},
            frm = null,
            oTree = null,
            response = null,
            elListItem = null,
            elList = null;

        try {
          // Check for 'main'
          if (sPart !== undefined && sPart === "main") {
            // THis means: return to the main center          
            $(".result-part").addClass("hidden");
            $(".result-part").removeClass("active");
            $("#goto_result_details").addClass("hidden");
            $("#action_buttons").removeClass("hidden");
            $("#result_info").removeClass("hidden");
            $("#result_host_containers").addClass("hidden");
            $("#result_filter_list").removeClass("hidden");
            return;
          }

          // Make sure we hide the jumbo buttons and the search result information
          $("#action_buttons").addClass("hidden");
          $("#result_info").addClass("hidden");
          $("#result_host_containers").removeClass("hidden");
          $("#result_wait_message").removeClass("hidden");
          $("#result_filter_list").addClass("hidden");

          frm = $("#qc_form");
          if (frm !== undefined) {
              data = $(frm).serializeArray();
              // Some items need data added
              switch (sPart) {
                  case "4":
                  case "5":
                      data.push({ 'name': 'resid', 'value': $(el).attr('resid') });
                      break;
              }
          }

          // Get the correct target id: a 'result_container_{num}'
          sTargetId = "#" + sTargetId + sPart;
          // Clear errors
          private_methods.errClear();
          // Get the correct id for this BASKET
          sObjectId = $("#basketid").text().trim();

          // [2] Load the new form through an AJAX call
          sAjaxMethod = "GET";
          var ajaxurl = $(el).attr("targeturl");
          switch (sPart) {
            case "2":
              sAjaxMethod = "POST";
            case "1":
            case "3":
            case "4":
            case "5":
              // CHeck if we need to take another instance id instead of #researchid
              if ($(el).attr("instanceid") !== undefined) { sObjectId = $(el).attr("instanceid"); }

              // POST call: show waiting
              $("#kwic-fetch").removeClass("hidden");
              // Fetch the correct data through a POST call
              response = ru.cesar.seeker.ajaxcall(ajaxurl, data, sAjaxMethod);
              if (response !== undefined && response.status && response.status === 'ok') {
                // Make the HTML response visible in a 'result_container_{num}'
                $(sTargetId).html(response.html);
                // Make sure events are set again
                ru.cesar.seeker.init_events();
              }
              // POST call: hide waiting
              $("#kwic-fetch").addClass("hidden");
              break;
          }
          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);

          // Hide all research parts
          $(".result-part").not(sTargetId).addClass("hidden");
          $(".result-part").not(sTargetId).removeClass("active");

          // Show the target result part
          $(sTargetId).removeClass("hidden");

          // Show the 'back' button and hide ourselves
          switch (sPart) {
            case "1": case "2": case "3":
              $("#goto_result_details").removeClass("hidden");
              $("#goto_finetune").addClass("hidden");
              break;
            case "5":
              // Show the tree in the appropriate location
              oTree = JSON.parse( response.sent_info.allT);
              crpstudio.svg.treeToSvg("#sentdetails_tree", oTree, "#sentdetails_err");
              break;
          }
          $("#result_wait_message").addClass("hidden");


        } catch (ex) {
          private_methods.errMsg("result_wizard", ex);
        }
      },

      /**
       * research_wizard
       *    Select one item from the research project wizard
       *
       */
      research_wizard: function (el, sPart) {
        var sTargetId = "research_container_",
            sTargetType = "",
            sObjectId = "",
            sMsg = "",
            html = "",
            data = {},
            frm = null,
            response = null,
            elWait = null,      // Div that should be opened/closed to indicate waiting
            elListItem = null,
            elList = null;

        try {
          // Set waiting div
          elWait = private_methods.waitInit(el);
          // Start waiting
          private_methods.waitStart(elWait);
          
          // Get the correct target id
          sTargetId = "#" + sTargetId + sPart;
          sObjectId = $("#researchid").text().trim();
          sTargetType = $("#id_research-targetType").val();
          // If it is undefined, try to get the target type from the input
          if (sTargetType === undefined || sTargetType === "") {
            sTargetType = $("#targettype").text().trim();
          }
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
                // Stop waiting
                private_methods.waitStop(elWait);
                // We need to LEAVE at this point
                return;
            }
          }
          // Find the currently shown 'research-part' form
          frm = $(".research-part").not(".hidden").find("form");
          // [1] Some (increasingly many) calls require FIRST saving of the currently loaded information
          sMsg = "";
          switch (sPart) {
            case "42": sMsg = "4-before-42";
            case "43": if (sMsg === "") sMsg = "42-before-43";
            case "44": if (sMsg === "") sMsg = "43-before-44";
            case "62": if (sMsg === "") sMsg = "6-before-62";
            case "63": if (sMsg === "") sMsg = "62-before-63";
              // Opening a new form requires prior processing of the current form
              if (frm !== undefined) {
                data = $(frm).serializeArray();
                var button = $(frm).find(".submit-row .ajaxform");
                if (button !== undefined) {
                  // Indicate we are saving
                  $(".save-warning").html("Processing... " + sMsg + loc_sWaiting);
                  data.push({ 'name': 'instanceid', 'value': $(button).attr("instanceid") });
                  // Process this information: save the data!
                  response = ru.cesar.seeker.ajaxcall($(button).attr("ajaxurl"), data, "POST");
                  // Check the response
                  if (response.status === undefined || response.status !== "ok") {
                    // Action to undertake if we have not been successfull
                    private_methods.errMsg("research_wizard[" + sPart + "]: could not save the data for this function");
                    // Stop waiting
                    private_methods.waitStop(elWait);
                    // And leave...
                    return;
                  }
                }
              }
              break;
          }

          // [2] Load the new form through an AJAX call
          data = [];
          switch (sPart) {
            case "62":
              // If a new condition has been created, then this is where we expect the instance number to appear
              if ('cond_instanceid' in response) {
                $(el).attr("instanceid", response['cond_instanceid']);
              }
              // data.push({ 'name': 'research_id', 'value': sObjectId });
            case "1":
            case "2":
            case "3":
            case "4":
            case "42":
            case "43":
            case "44":
            case "6":
            case "63":

              // CHeck if we need to take another instance id instead of #researchid
              if ($(el).attr("instanceid") !== undefined) { sObjectId = $(el).attr("instanceid"); }
              // Indicate we are saving/preparing
              $(".save-warning").html("Processing... " + sPart + loc_sWaiting);
              // Fetch the corr
              response = ru.cesar.seeker.ajaxform_load($(el).attr("targeturl"), sObjectId, data);
              if (response.status && response.status === "ok") {
                // Make the HTML response visible
                $(sTargetId).html(response.html);
                // Make sure events are set again
                ru.cesar.seeker.init_events();
              }
              break;
          }
          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);

          // Some actions depend on the particular page we are going to visit
          switch (sPart) {
            case "4": // Page 4=Calculation
            case "42":
              // add any event handlers for wizard part '42'
              ru.cesar.seeker.init_cvar_events();
              break;
            case "43":
            case "44":
            case "62":
            case "63":
              // add any event handlers for wizard part '43' and part '44'
              // As well as for '62' and '63'
              ru.cesar.seeker.init_arg_events();
              break;
            case "6":
              // add any event handlers for wizard part '46'
              ru.cesar.seeker.init_cond_events();
              // Specify the function to be called when the user presses "summary"
              // $(".func-summary").click(function () { ru.cesar.seeker.get_summary_click(this, "#cond_summary"); });
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
              $(".func-summary").click(function () { ru.cesar.seeker.get_summary_click(this, "#cvar_summary"); });
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
              $(elList).children('button').each(function () {
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
          // Hide the tiles and show the contents
          $("#research_tiles").addClass("hidden");
          $("#research_contents").removeClass("hidden");
          $("#research_conditions").addClass("hidden");
          switch (sPart) {
            case "1": case "2": case "7":
              $("#goto_overview").removeClass("hidden");
              $("#goto_finetune").addClass("hidden");
              break;
            case "3": case "4": case "42": case "43":
            case "44": case "6":
              $("#goto_overview").addClass("hidden");
              $("#goto_finetune").removeClass("hidden");
              break;
          }
          // Stop waiting
          private_methods.waitStop(elWait);
        } catch (ex) {
          private_methods.errMsg("research_wizard", ex);
          // Stop waiting
          private_methods.waitStop(elWait);
        }
      },

      /**
       * search_start
       *   Check and then start a search
       *
       */
      search_start(elStart) {
        var sDivProgress = "#research_progress",
            ajaxurl = "",
            response = null,
            basket_id = -1,
            frm = null,
            sMsg = "",
            data = [];

        try {
          // Clear the errors
          private_methods.errClear();

          // obligatory parameter: ajaxurl
          ajaxurl = $(elStart).attr("ajaxurl");

          // Gather the information
          frm = $(elStart).closest("form");
          if (frm !== undefined) { data = $(frm).serializeArray(); }

          // Start the search
          $(sDivProgress).html("Contacting the search server")

          // Hide some buttons
          $("#research_stop").addClass("hidden");
          $("#research_results").addClass("hidden");

          // Make an AJAX call to get an existing or new specification element HTML code
          response = ru.cesar.seeker.ajaxcall(ajaxurl, data, "POST");
          if (response.status === undefined) {
            // Show an error somewhere
            private_methods.errMsg("Bad execute response");
            $(sDivProgress).html("Bad execute response:<br>"+response);
          } else if (response.status === "error") {
            // Show the error that has occurred
            if ("html" in response) { sMsg = response['html']; }
            if ("error_list" in response) { sMsg += response['error_list']; }
            private_methods.errMsg("Execute error: " + sMsg);
            $(sDivProgress).html("execution error");
          } else {
            // All went well -- get the basket id
            basket_id = response.basket_id;
            basket_progress = response.basket_progress;
            basket_stop = response.basket_stop;
            basket_result = response.basket_result;
            basket_data = data;
            // Make the stop button available
            $("#research_stop").removeClass("hidden");
            // TODO: hide the start button
            // $("#research_start").addClass("hidden");

            // Start the next call for status after 1 second
            setTimeout(function () { ru.cesar.seeker.search_progress(); }, 1000);
          }


        } catch (ex) {
          private_methods.errMsg("search_start", ex);
        }
      },

      /**
       * search_stop
       *   Stop an already going search
       *
       */
      search_stop() {
        var sDivProgress = "#research_progress",
            response = null;
        try {
          // Make an AJAX call by using the already stored basket_stop URL
          response = ru.cesar.seeker.ajaxcall(basket_stop, basket_data, "POST");
          if (response.status !== undefined) {
            switch (response.status) {
              case "ok": break;
              case "error": break;
            }
          }

        } catch (ex) {
          private_methods.errMsg("search_stop", ex);
        }
      },

      /**
       * search_progress
       *   Elicit and show the status of an ongoing search
       *
       */
      search_progress() {
        var sDivProgress = "#research_progress",
            response = null,
            html = [],
            sMsg = "";

        try {
          // Make an AJAX call by using the already stored basket_stop URL
          response = ru.cesar.seeker.ajaxcall(basket_progress, basket_data, "POST");
          if (response.status !== undefined) {
            if ('html' in response) { sMsg = response.html; }
            switch (response.status) {
              case "ok":
                // Action depends on the statuscode
                switch (response.statuscode) {
                  case "working":
                    // Show the status of the project
                    $(sDivProgress).html(response.html);
                    // Make sure we are called again
                    setTimeout(function () { ru.cesar.seeker.search_progress(); }, 500);
                    break;
                  case "completed":
                    // Show that the project has finished
                    $(sDivProgress).html(response.html);
                    // Hide the STOP button
                    $("#research_stop").addClass("hidden");
                    // Show the RESULTS button
                    $("#research_results").removeClass("hidden");
                    // Set the correct href for the button
                    $("#research_results").attr("href", basket_result);
                    break;
                  default:
                    // Show the current status
                    private_methods.errMsg("Unknown statuscode: [" + response.status.statuscode+"]");
                    break;
                }
                break;
              case "error":
                if ('error_list' in response) { sMsg += response.error_list; }
                private_methods.errMsg("Progress error: " + sMsg);
                break;
            }
          }

        } catch (ex) {
          private_methods.errMsg("search_progress", ex);
        }
      },

      /**
       * select_qc
       *   Set the 'qc' to the correct div and then open [sDivOpen]
       *
       */
      select_qc: function (elThis, sDivQc, sDivOpen) {
        try {
          var iSelectedQc = parseInt($(elThis).val(), 10);
          $("#"+sDivQc).html(str(iSelectedQc));
          $("#" + sDivOpen).removeClass("hidden");
        } catch (ex) {
          private_methods.errMsg("select_qc", ex);
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
       * tabular_addrow
       *   Add one row into a tabular inline
       *
       */
      tabular_addrow: function () {
        //var arTable = ['research_intro-wrd', 'research_intro-cns', 'research_gvar', 'research_vardef', 'research_spec', 'research_cond'],
        //    arPrefix = ['construction', 'construction', 'gvar', 'vardef', 'function', 'cond'],
        //    arNumber = [true, true, false, false, false, true],
        var arTdef = lAddTableRow,
            oTdef = {},
            elTable = null,
            iNum = 0,     // Number of <tr class=form-row> (excluding the empty form)
            sId = "",
            i;

        try {
          // Find out just where we are
          sId = $(this).closest("div").attr("id");
          // Walk all tables
          for (i = 0; i < arTdef.length; i++) {
            // Get the definition
            oTdef = arTdef[i];
            if (sId === oTdef.table || sId.indexOf(oTdef.table) >= 0) {
              // Go to the <tbody> and find the last form-row
              elTable = $(this).closest("tbody").children("tr.form-row.empty-form")

              // Perform the cloneMore function to this <tr>
              ru.cesar.seeker.cloneMore(elTable, oTdef.prefix, oTdef.counter);
              // Call the event initialisation again
              if (oTdef.events !== null) {
                oTdef.events();
              }
              // We are done...
              break;
            }
          }
        } catch (ex) {
          private_methods.errMsg("tabular_addrow", ex);
        }
      },

      /**
       * task_save
       *   Perform the SAVE function with an additional task
       *
       */
      task_save: function (sTask, elThis, function_id) {
        var divTarget = null, // The select function
            divSave = null;   // THe save button

        try {
          divTarget = $(elThis).parent().find("select").first();
          if (sTask !== undefined && function_id !== undefined && divTarget !== null) {
            // Prepare data
            var data = []
            data.push({ 'name': 'task', 'value': sTask });
            data.push({ 'name': 'functionid', 'value': function_id });
            data.push({ 'name': 'constructionid', 'value': $(divTarget).val() });
            // Find out where the save button is located
            divSave = $(elThis).closest("form").find(".submit-row button").first();
            if (divSave !== null) {
              // Position the data in place
              $(divSave).attr("data", JSON.stringify( data));
              // Simulate pressing the 'SAVE' button with these data
              ru.cesar.seeker.ajaxform_click.call(divSave);
            }
          }
        } catch (ex) {
          private_methods.errMsg("task_save", ex);
        }
      },

      /**
       *  toggle_del
       *      Toggle research item
       *
       */
      toggle_del: function (el) {
        var elTr = null;

        try {
          // Get to the nearest <tr>
          elTr = $(el).closest("tr");
          // Is this .part-del?
          if ($(elTr).is(".part-del")) {
            // Hide it
            $(elTr).addClass("hidden");
          } else {
            // Get to the next .part-del
            elTr = $(elTr).next(".part-del");
            // Show it
            $(elTr).removeClass("hidden");
            // Also make sure the correct contents is shown
            $(elTr).find(".part-del").removeClass("hidden");
            $(elTr).find(".part-process").addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("toggle_del", ex);
        }
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


      var_down: function() {private_methods.var_move(this, 'down');},
      var_up: function () { private_methods.var_move(this, 'up'); },


    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

