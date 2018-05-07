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
        basket_start = "",            // URL to start Translation + Execution
        basket_stop = "",             // URL to stop the basket
        basket_watch = "",            // URL to watch basket that is in progress
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
          { "table": "research_feat", "prefix": "feat", "counter": true, "events": function () { ru.cesar.seeker.init_feat_events(); } },
          { "table": "result_kwicfilter", "prefix": "filter", "counter": true, "events": null },
      ];


    // Private methods specification
    var private_methods = {
      /**
       * fitFeatureBox
       *    Initialize the <svg> in the @sDiv
       * 
       * @param {object} oBound
       * @param {el} elTarget
       * @returns {object}
       */
      fitFeatureBox: function (oBound, elTarget) {
        var rect = null;

        try {
          // Take into account scrolling
          oBound['x'] -= document.documentElement.scrollLeft || document.body.scrollLeft;
          oBound['y'] -= document.documentElement.scrollTop || document.body.scrollTop;
          // Make sure it all fits
          if (oBound['x'] + $(elTarget).width() + oBound['width'] + 10 > $(window).width()) {
            oBound['x'] -= $(elTarget).width() + oBound['width'];
          } else if (oBound['x'] < 0) {
            oBound['x'] = 10;
          }
          if (oBound['y'] + $(elTarget).height() + oBound['height'] + 10 > $(window).height()) {
            oBound['y'] -= $(elTarget).height() + oBound['height'];
          } else if (oBound['y'] < 0) {
            oBound['y'] = 10;
          } else {
            oBound['y'] += oBound['height'] + 10;
          }
          // Take into account scrolling
          oBound['x'] += document.documentElement.scrollLeft || document.body.scrollLeft;
          oBound['y'] += document.documentElement.scrollTop || document.body.scrollTop;
          return oBound;
        } catch (ex) {
          private_methods.showError("fitFeatureBox", ex);
          return oBound;
        }
      },
      /**
       * methodNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      methodNotVisibleFromOutside: function () {
        return "something";
      },

      /**
       * prepend_styles
       *    Get the html in sDiv, but prepend styles that are used in it
       * 
       * @param {el} HTML dom element
       * @returns {string}
       */
      prepend_styles: function (sDiv, sType) {
        var lData = [],
            el = null,
            i, j,
            sheets = document.styleSheets,
            used = "",
            elems = null,
            tData = [],
            rules = null,
            rule = null,
            s = null,
            sSvg = "",
            defs = null;

        try {
          // Get the correct element
          if (sType === "svg") { sSvg = " svg";}
          el = $(sDiv + sSvg).first().get(0);
          // Get all the styles used 
          for (i = 0; i < sheets.length; i++) {
            rules = sheets[i].cssRules;
            for (j = 0; j < rules.length; j++) {
              rule = rules[j];
              if (typeof (rule.style) !== "undefined") {
                elems = el.querySelectorAll(rule.selectorText);
                if (elems.length > 0) {
                  used += rule.selectorText + " { " + rule.style.cssText + " }\n";
                }
              }
            }
          }

          // Get the styles
          s = document.createElement('style');
          s.setAttribute('type', 'text/css');
          switch (sType) {
            case "html":
              s.innerHTML = used;

              // Get the table
              tData.push("<table class=\"func-view\">");
              tData.push($(el).find("thead").first().get(0).outerHTML);
              tData.push("<tbody>");
              $(el).find("tr").each(function (idx) {
                if (idx > 0 && !$(this).hasClass("hidden")) {
                  tData.push(this.outerHTML);
                }
              });
              tData.push("</tbody></table>");

              // Turn into a good HTML
              lData.push("<html><head>");
              lData.push(s.outerHTML);
              lData.push("</head><body>");
              // lData.push(el.outerHTML);
              lData.push(tData.join("\n"));
              
              lData.push("</body></html>");
              break;
            case "svg":
              s.innerHTML = "<![CDATA[\n" + used + "\n]]>";

              defs = document.createElement('defs');
              defs.appendChild(s);
              el.insertBefore(defs, el.firstChild);

              el.setAttribute("version", "1.1");
              el.setAttribute("xmlns", "http://www.w3.org/2000/svg");
              el.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
              lData.push("<?xml version=\"1.0\" standalone=\"no\"?>");
              lData.push("<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\" >");
              lData.push(el.outerHTML);
              break;
          }

          return lData.join("\n");
        } catch (ex) {
          private_methods.showError("prepend_styles", ex);
          return "";
        }
      },

      /**
       * screenCoordsForRect
       *    Get the correct screen coordinates for the indicated <svg> <rect> element
       * 
       * @param {el} svgRect
       * @returns {object}
       */
      screenCoordsForRect: function (svgRect) {
        var pt = null,
            elSvg = null,
            rect = null,
            oBound = {},
            matrix;

        try {
          // Get the root <svg>
          elSvg = $(svgRect).closest("svg").get(0);

          rect = svgRect.get(0);
          oBound = rect.getBoundingClientRect();

          // Take into account scrolling
          oBound['x'] += document.documentElement.scrollLeft || document.body.scrollLeft;
          oBound['y'] += document.documentElement.scrollTop || document.body.scrollTop;
          return oBound;
        } catch (ex) {
          private_methods.showError("screenCoordsForRect", ex);
          return oBound;
        }

      },
      /**
       *  var_move
       *      Move variable row one step down or up
       *      This means the 'order' attribute changes
       */
      var_move: function (elStart, sDirection, sType) {
        var elRow = null,
            el = null,
            tdCounter = null,
            rowSet = null,
            iLen = 0;

        try {
          // Find out what type we have
          if (sType === undefined) { sType = ""; }
          switch (sType) {
            case "selected":
              // Find the selected row
              elRow = $(elStart).closest("form").find("tr.selected").first();
              // The element is below
              el = $(elRow).find(".var-order input").parent();
              break;
            default:
              // THe [el] is where we start
              el = elStart;
              // The row is above me
              elRow = $(el).closest("tr");
              break;
          }
          // Perform the action immediately
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
              // Look for a <td> element with class "counter"
              tdCounter = $(el).find("td.counter");
              if (tdCounter.length > 0) {
                $(tdCounter).html(index+1);
              }
            }
            if (sType === "") {
              // Check visibility of up and down
              $(el).find(".var-down").removeClass("hidden");
              $(el).find(".var-up").removeClass("hidden");
              if (index === 0) {
                $(el).find(".var-up").addClass("hidden");
              }
              if (index === iLen - 1) {
                $(el).find(".var-down").addClass("hidden");
              }
            }
          });
        } catch (ex) {
          private_methods.errMsg("var_move", ex);
        }
      },
      errMsg: function (sMsg, ex) {
        var sHtml = "";
        // Replace newlines by breaks
        sMsg = sMsg.replace(/\n/g, "\n<br>");
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
      mainWaitStart : function() {
        var elWait = $(".main-wait").first();
        if (elWait !== undefined && elWait !== null) {
          $(elWait).removeClass("hidden");
        }
      },
      mainWaitStop: function () {
        var elWait = $(".main-wait").first();
        if (elWait !== undefined && elWait !== null) {
          $(elWait).addClass("hidden");
        }
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
       * argrow_click
       *   Show or hide the following <tr> element
       *   Also: adapt the +/- sign(s)
       */
      argrow_click: function (el, sClass, bShow) {
        var trNext = null;

        try {
          // Validate
          if (el === undefined) { return; }
          // Get the following <tr>
          trNext = $(el).closest("tr").next().first();
          if (trNext !== null) {
            // Check its current status
            if ($(trNext).hasClass("hidden") || (bShow !== undefined && bShow)) {
              // Show it
              $(trNext).removeClass("hidden");
              // Change the '+' into a '-'
              $(el).html("-");
            } else {
              // Hide it
              $(trNext).addClass("hidden");
              // Change the '-' into a '+'
              $(el).html("+");
              // Hide all underlying ones with class [sClass]
              if (sClass !== undefined && sClass !== "") {
                $(trNext).find("." + sClass).addClass("hidden");
                $(trNext).find(".arg-plus").html("+");
              }
            }
          }

        } catch (ex) {
          private_methods.errMsg("argrow_click", ex);
        }
      },
      /**
       * funchead_click
       *   Assuming we are on an element of class [func-plus]
       *     - close or open everything with style [sClass] below us
       *     - this depends on the 'sign' we have: + or -
       *   Also: adapt the +/- sign(s)
       */
      funchead_click: function (el, sClass) {
        var trNext = null,
            elTbody = null, // My own <tbody>
            sStatus = "";   // My own status

        try {
          // Validate
          if (el === undefined) { return; }
          // Get my status
          sStatus = $(el).text();   // This can be + or -
          // Get my own <tbody>
          elTbody = $(el).closest("table").children("tbody").first();
          // Check status
          if (sStatus == "-") {
            // We are open and need to close all below
            $(el).html("+");
            $(el).attr("title", "open");
            // Close all [arg-plus] below us
            $(elTbody).find(".arg-plus").html("+");
            $(elTbody).find(".func-plus").html("+");
            $(elTbody).find(".func-plus").attr("title", "open");
            $(elTbody).find(".func-inline").addClass("hidden");
          } else {
            // We are + (=closed) and need to open (become -)
            $(el).html("-");
            $(el).attr("title", "close");
            // Open all [arg-plus] below us
            $(elTbody).find(".arg-plus").html("-");
            $(elTbody).find(".func-plus").html("-");
            $(elTbody).find(".func-plus").attr("title", "close");
            $(elTbody).find(".func-inline").removeClass("hidden");
          }

        } catch (ex) {
          private_methods.errMsg("funchead_click", ex);
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
          $(elVal).find(".arg-value").addClass("hidden");
          $(elVal).find(".arg-expression").addClass("hidden");
          $(elVal).find(".arg-gvar").addClass("hidden");
          $(elVal).find(".arg-cvar").addClass("hidden");
          $(elVal).find(".arg-dvar").addClass("hidden");
          $(elVal).find(".arg-rcnst").addClass("hidden");
          $(elVal).find(".arg-raxis").addClass("hidden");
          $(elVal).find(".arg-rcond").addClass("hidden");
          $(elVal).find(".arg-search").addClass("hidden");
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
            case "raxis":  // Relation - axis
              $(elVal).find(".arg-raxis").removeClass("hidden");
              break;
            case "rcond":  // Relation - condition
              $(elVal).find(".arg-rcond").removeClass("hidden");
              break;
            case "rcnst":  // Relation - constituent
              $(elVal).find(".arg-rcnst").removeClass("hidden");
              break;
            case "hit":  // Search hit
              $(elVal).find(".arg-search").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("argtype_click", ex);
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
          // Initialisations
          response['status'] = "initializing";
          // Validate
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
            error: function (jqXHR, textStatus, errorThrown) {
              var sMsg = "The ajaxcall [" + textStatus + "] returns an error response: " + jqXHR.responseText;
              private_methods.errMsg(sMsg);
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
            extra = [],     // Additional data
            elErr = null,   // The 'research_err' component under the <form>
            i,
            elCall = this,
            response = null,
            elWait = null,
            action = "",
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
          var elStart = $(this);
          var bNew = (instanceid.toString() === "None");
          action = $(this).attr("action");

          // Derive the data
          if ($(this).attr("data")) {
            data = $(this).attr("data");
          } else {
            var frm = $(this).closest("form");
            if (frm !== undefined) {
              data = $(frm).serializeArray();
              // Check if there is additional data
              if ($(this).attr("extra")) {
                extra = JSON.parse($(this).attr("extra"));
                for (i = 0; i < extra.length; i++) {
                  data.push(extra[i]);
                }
              }
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
              // Set a tag to indicate that we need to jump to a new item when returning
              $(elOview).attr("isnew", true);
            }
          }
          // Check whether we need to show the error response
          if ('has_errors' in response && response.has_errors) {
            // See if there is a 'research_err' component under the <form>
            elErr = $(this).closest("form").find("#research_err").first();
            // Do we have an 'err_view' html contents?
            if ('err_view' in response && elErr !== null) {
              $(elErr).html(response.err_view);
            } else {
              // Yes, show the resulting form with the errors
              $(elOpen).html(response.html);
            }
            // Make sure events are set again
            ru.cesar.seeker.init_events();
            // Bind the click event to all class="ajaxform" elements
            $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);
            // Stop waiting
            private_methods.waitStop(elWait);
            // Show that errors need to be repaired
            $(".save-warning").html("(not saved; there are errors)");
            // And return
            return;
          }

          // Continuation depends on the action
          switch (action) {
            case "save_function":
              // Show we are showing the function summary
              $('.save-warning').html("Updating the summary...");
              // Showing the summary
              var funcsum = $(elStart).closest(".func_summary");
              var targeturl = "";
              if (funcsum !== null) {
                targeturl = $(funcsum).attr("targeturl");
              }
              ru.cesar.seeker.get_summary_show("", targeturl, instanceid);
              // Remove the save warning
              $('.save-warning').html("");
              break;
            default:
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
                  case "research_container_72":
                  case "research_container_73":
                    // add any event handlers for wizard part '43' and '44' and '62'
                    ru.cesar.seeker.init_arg_events();
                    break;
                  case "research_container_6":
                    // add any event handlers for wizard part '46'
                    ru.cesar.seeker.init_cond_events();
                    break;
                  case "research_container_7":
                    // add any event handlers for wizard part '46'
                    ru.cesar.seeker.init_feat_events();
                    break;
                }
              }
              break;
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
          if (instanceid !== undefined && instanceid !== '' && instanceid !== "None" ) {
            // First check if we already have a sequence of /nnn/
            if (!/\/\d+\//.test(ajaxurl) && ajaxurl.indexOf('/' + instanceid + "/") < 0) {
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
       * corpus_refine
       *   Refine search selection
       *
       */
      corpus_refine: function (el, sTarget) {
        var divTarget = "",
            divOption = null, // Chosen <option>
            sChosen = "";     // Option that has been chosen

        try {
          // Get the target <div>
          divTarget = "#" + sTarget;
          // Find out what has been chosen
          sChosen = $(el).val();
          if (sChosen !== undefined && sChosen !== "") {
            switch (sChosen) {
              case "-":
              case "all":
                // Hide the target
                $(divTarget).addClass("hidden");
                break;
              default:
                // Show the target
                $(divTarget).removeClass("hidden");
                break;
            }
          }

        } catch (ex) {
          private_methods.errMsg("corpus_refine", ex);
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
       * feattype_click
       *   Set the type of feature: dvar versus func
       *
       */
      feattype_click: function (el) {
        try {
          var elRow = (el.target === undefined) ? el : $(this).closest("tr");
          var elType = $(elRow).find(".feat-type").first();
          var elVal = $(elRow).find(".feat-val-exp").first();
          // Find the type element
          var elfeattype = $(elType).find("select").first();
          // Get its value
          var elfeattypeVal = $(elfeattype).val();
          // Hide/show, depending on the value
          switch (elfeattypeVal) {
            case "dvar": // Data-dependant variable
              $(elVal).find(".feat-dvar").removeClass("hidden");
              $(elVal).find(".feat-expression").addClass("hidden");
              break;
            case "func": // Function
              $(elVal).find(".feat-dvar").addClass("hidden");
              $(elVal).find(".feat-expression").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("feattype_click", ex);
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
      get_summary_click: function (el, target, bShow) {
        var response,   // The ID of the current row
            targeturl = "",
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
          // Store the target url
          targeturl = $(el).attr("targeturl");
          // Is it closed or opened?
          if ($(elSum).hasClass("hidden") || (bShow !== undefined && bShow)) {
            ru.cesar.seeker.get_summary_show(sTargetId, targeturl);
          } else {
            // Hide it
            $(elSum).addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("get_summary_click", ex);
        }
      },

      /**
       * get_summary_click
       *   Show the summary of the expression fetched from [targeturl]
       *
       */
      get_summary_show: function (target, targeturl, instanceid) {
        var response,   // The ID of the current row
            elSum = null,
            elInstance = null,
            sTargetId = "#cvar_summary";

        try {
          // Possibly get target
          if (target !== undefined && target !== "") {
            sTargetId = target;
          }
          // Find the expression summary
          elSum = $(sTargetId);
          // Calculate and show the value
          response = ru.cesar.seeker.ajaxform_load(targeturl);
          if (response.status && response.status === "ok") {
            // Make the HTML response visible
            $(elSum).html(response.html);
            // Make sure events are set again
            ru.cesar.seeker.init_events();
          }
          // Copy the 'targeturl' attribute
          if (targeturl !== undefined && targeturl !== "") {
            // Add the targeturl to the summary element
            $(elSum).attr('targeturl', targeturl);
          }
          // Unhide it
          $(elSum).removeClass("hidden");
          // Has an instanceid been specified?
          if (instanceid !== undefined && instanceid !== "") {
            // Find the element with this instanceid
            elInstance = $(elSum).find("[instanceid='" + instanceid + "']").first();
            if (elInstance !== null) {
              // Show this one and all those above it
              $(elInstance).parents(".func-view").removeClass("hidden");
            }
          }
        } catch (ex) {
          private_methods.errMsg("get_summary_show", ex);
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
       *  init_feat_events
       *      Bind events to work with featitions
       *
       */
      init_feat_events: function () {
        try {
          // Make sure the 'Type' field values are processed everywhere
          $(".feat-item").each(function () {
            // Perform the same function as if we were clicking it
            ru.cesar.seeker.feattype_click(this);
          });
          // Specify the change reaction function
          $(".feat-type select").change(ru.cesar.seeker.feattype_click);
          // Specify the function to be called when the user presses "summary"
          $(".func-summary").unbind('click');
          $(".func-summary").click(function () { ru.cesar.seeker.get_summary_click(this, "#feat_summary"); });
        } catch (ex) {
          private_methods.errMsg("init_feat_events", ex);
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
       *  form_row_select
       *      Select or unselect a form-row
       *
       */
      form_row_select: function () {
        var elTable = null,
            elRow = null,     // The row
            iSelCount = 0,    // Number of selected rows
            bSelected = false;

        try {
          // Get to the row
          elRow = $(this).closest("tr.form-row");
          // Get current state
          bSelected = $(elRow).hasClass("selected");
          // FInd nearest table
          elTable = $(elRow).closest("table");
          // Check if anything other than me is selected
          iSelCount = 1;
          // Remove all selection
          $(elTable).find(".form-row.selected").removeClass("selected");
          // CHeck what we need to do
          if (bSelected) {
            // We are de-selecting: hide the 'Up' and 'Down' buttons if needed
            ru.cesar.seeker.show_up_down(this,false);
          } else {
            // Select the new row
            $(elRow).addClass("selected");
            // SHow the 'Up' and 'Down' buttons if needed
            ru.cesar.seeker.show_up_down(this,true);
          }

        } catch (ex) {
          private_methods.errMsg("form_row_select", ex);
        }
      },

      /**
       *  show_up_down
       *      Show or hide up/down buttons
       *      But only do this if the table has a row that has elements with class ".var-order"
       *
       */
      show_up_down: function (el, bShow) {
        var bHasOrder = false,  // THis table has 'order'
            divSubmit = null,   // Submit row
            divUp = null,       // Button to move up
            divDown = null;     // Button to move down

        try {
          // DO we have order?
          bHasOrder = ($(el).closest("table").find(".var-order").first().length > 0);
          if (!bHasOrder) { return; }
          // We have order: find the buttons
          divSubmit = $(el).closest("form").find("div.submit-row").first();
          if (divSubmit.length === 0) { return;}
          divUp = $(divSubmit).find("span.row-up").first();
          divDown = $(divSubmit).find("span.row-down").first();
          // Check out the buttons
          if (divUp.length === 0) {
            // Create an UP button
            $(divSubmit).prepend("<span class='btn btn-primary row-up glyphicon glyphicon-chevron-up' title='move upwards'></span>");
            divUp = $(divSubmit).find("span.row-up").first();
            // bind click event
            $(divUp).on("click", function () {
              private_methods.var_move(this, 'up', 'selected');
            });
          }
          if (divDown.length === 0) {
            // create a DOWN button
            $(divSubmit).prepend("<span class='btn btn-primary row-down glyphicon glyphicon-chevron-down' title='move downwards'></span>");
            divDown = $(divSubmit).find("span.row-down").first();
            // bind click event
            $(divDown).on("click", function () {
              private_methods.var_move(this, 'down', 'selected');
            });
          }
          // We have order: show or hide buttons
          if (bShow) {
            // Show the buttons
            divUp.removeClass("hidden");
            divDown.removeClass("hidden");
          } else {
            // Hide the buttons
            divUp.addClass("hidden");
            divDown.addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("show_up_down", ex);
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
          $('span.td-toggle-textarea').unbind('click').click(ru.cesar.seeker.toggle_textarea_click);
          $('input.td-toggle-textarea').unbind('click').click(ru.cesar.seeker.toggle_textarea_click);
          // Make sure variable ordering is supported
          $('td span.var-down').unbind('click').click(ru.cesar.seeker.var_down);
          $('td span.var-up').unbind('click').click(ru.cesar.seeker.var_up);

          // Allow form-row items to be selected or unselected
          $('tr.form-row').each(function () {
            // Add it to the first visible cell
            $(this).find("td").not(".hidden").first().unbind('click').click(ru.cesar.seeker.form_row_select);
            // Make sure any other cells  that have an <input> or a <td-toggle-textarea> are set too
            $(this).find("td").not(".hidden").each(function () {
              if ($(this).find("input").length > 0 ||
                  $(this).find("span.td-toggle-textarea").length > 0) {
                $(this).unbind("click").click(ru.cesar.seeker.form_row_select);
              }
            });
          });

          // Make sure all <input> elements in a <form> are treated uniformly
          $("form input[type='text']").each(function () {
            var $this = $(this),
                $span = $this.prev("span");
            // Create span if not existing
            if ($span === undefined || $span === null || $span.length === 0) {
              $span = $this.before("<span></span");
              // Still need to go to the correct function
              $span = $this.prev("span");
            }
            // Set the value of the span
            $span.html($this.val());
            // Now specify the action on clicking the span
            $span.on("click", function () {
              var $this = $(this);
              $this.hide().siblings("input").show().focus().select();
            });
            // Specify what to do on blurring the input
            $this.on("blur", function () {
              var $this = $(this);
              // Show the value of the input in the span
              $this.hide().siblings("span").text($this.val()).show();
            }).on("keydown", function (e) {
              // SPecify what to do if the tab is pressed
              if (e.which === 9) {
                e.preventDefault();
                if (e.shiftKey) {
                  // Need to go backwards
                  $(this).blur().closest("tr").prev("tr").find("input[type='text']").not(".hidden").first().prev("span").click();
                } else {
                  // Move forwards
                  $(this).blur().closest("tr").next("tr").find("input[type='text']").not(".hidden").first().prev("span").click();
                }
              }
            });
            // Make sure the <input> is hidden, unless it is empty
            if ($this.val() !== "") {
              $this.hide();
            }
          });

          // Attach an event handler to all the NODES
          $("g.main-el").mouseover(function () { ru.cesar.seeker.main_info_show(this) });
          $("g.main-el").mouseout(function () { ru.cesar.seeker.main_info_hide(this) });

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

      research_watch: function (elThis, sDivName, sDivClose) {
        var sDivProgress = "#research_progress",
            frm = null,
            data = [],
            ajaxurl = "",
            elStart = "#select_part",
            basket_id = "",
            part_id = "";

        try {
          // First open the correct places
          ru.cesar.seeker.research_open(sDivName, sDivClose);
          // Get all the needed values
          basket_id = $(elThis).attr("basket_id");
          part_id = $(elThis).attr("part_id");
          ajaxurl = $(elThis).attr("ajaxurl");
          // Then select the correct corpus in the list
          $(elStart).val(part_id);
          // Make the stop button available
          $("#research_stop").removeClass("hidden");
          // Disable the START button
          $("#research_start").prop("disabled", true);
          // Show what we are attempting
          $(sDivProgress).html("Attempting to catch the search...");

          // Gather the information
          frm = $(elStart).closest("form");
          if (frm !== undefined) { data = $(frm).serializeArray(); }

          // All went well -- get the basket information
          $.post(ajaxurl, data, function (response) {
            if (response !== undefined) {
              switch (response.status) {
                case "ok":
                  basket_id = response.basket_id;
                  basket_start = response.basket_start;
                  basket_progress = response.basket_progress;
                  basket_stop = response.basket_stop;
                  basket_watch = response.basket_watch;
                  basket_result = response.basket_result;
                  basket_data = data;
                  // Now start calling for status updates
                  setTimeout(function () { ru.cesar.seeker.search_progress(); }, 500);
                  break;
                default:
                  private_methods.errMsg("research_watch: incorrect response " + response.status);
                  break;
              }
            }
          });


        } catch (ex) {
          private_methods.errMsg("research_watch", ex);
        }
      },

      /**
       * research_overview
       *   Show the tiles-overview
       *
       */
      research_overview : function(el) {
        var sTargetUrl = "",
            bIsNew = false;

        try {
          // Check if this is a new one
          bIsNew = $(el).attr("isnew");
          if (typeof bIsNew !== typeof undefined && bIsNew !== false) {
            // Try get the target url
            sTargetUrl = $(el).attr("targeturl");
            // Open this page
            window.location.href = sTargetUrl;
          } else {
            // New code: just show all the relevant places and hide the others
            ru.cesar.seeker.main_show_hide({
              "research_tiles": true, "action_buttons": true, "edit_buttons": true,
              "exe_dashboard": false, "goto_overview": false, "goto_finetune": false,
              "research_conditions": false, "research_contents": false
            });
          }

        } catch (ex) {
          private_methods.errMsg("research_overview", ex);
        }
      },

      /**
       * main_show_hide
       *    Show/hide elements on the main panel
       *
       */
      main_show_hide(options) {
        var sDiv = "",
            bShow = true;
        try {
          for (var item in options) {
            if (options.hasOwnProperty(item)) {
              sDiv = "#" + item;
              bShow = options[item];
              if (bShow) {
                $(sDiv).removeClass("hidden");
              } else {
                $(sDiv).addClass("hidden");
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("main_show_hide", ex);
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
            sUrl = "",
            sBackId = "",
            data = {},
            frm = null,
            oTree = null,
            response = null,
            elListItem = null,
            elList = null;

        try {
          // Check for 'main'
          if (sPart !== undefined && sPart === "main") {
            // Do we have a targeturl?
            sUrl = $(el).attr("targeturl");
            if (sUrl === undefined || sUrl === false) {
              // THis means: return to the main center          
              $(".result-part").addClass("hidden");
              $(".result-part").removeClass("active");
              $("#goto_result_details").addClass("hidden");
              $("#action_buttons").removeClass("hidden");
              $("#result_info").removeClass("hidden");
              $("#result_host_containers").addClass("hidden");
              $("#result_filter_list").removeClass("hidden");
              $("#downloadcenter").removeClass("hidden");
            } else {
              // Go to this url
              window.location.href = sUrl;
            }
            
            return;
          }

          // Make sure we hide the jumbo buttons and the search result information
          $("#action_buttons").addClass("hidden");
          $("#result_info").addClass("hidden");
          $("#result_host_containers").removeClass("hidden");
          $("#result_wait_message").removeClass("hidden");
          $("#result_filter_list").addClass("hidden");
          $("#downloadcenter").addClass("hidden");

          frm = $("#qc_form");
          if (frm !== undefined) {
              data = $(frm).serializeArray();
              // Some items need data added
              switch (sPart) {
                case "1":
                  //  Make sure [result_hide_empty] is shown
                  $("#result_hide_empty").removeClass("hidden");
                  // Set the value properly
                  $("#hide_empty").val($("#hide_empty").prop("checked"));
                  // Make sure 'hide_empty' gets pushed
                  data.push({ 'name': 'hide_empty', 'value': $("#hide_empty").prop("checked") });
                  break;
                case "2":
                  // Patch for now
                  data.push({ 'name': 'qc', 'value': '1'});
                  break;
                case "4":
                case "5":
                case "6":
                  data.push({ 'name': 'resid', 'value': $(el).attr('resid') });
                  // Do we have a backid?
                  sBackId = $(el).attr("backid");
                  if (sBackId !== undefined && sBackId !== "") {
                    data.push({ 'name': 'backid', 'value': sBackId });
                  }
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
            case "6":
              // CHeck if we need to take another instance id instead of #researchid
              if ($(el).attr("instanceid") !== undefined) { sObjectId = $(el).attr("instanceid"); }

              // POST call: show waiting
              $("#kwic-fetch").removeClass("hidden");
              // Fetch the correct data through a POST call
              response = ru.cesar.seeker.ajaxcall(ajaxurl, data, sAjaxMethod);
              if (response === undefined) {
                // serious business -- can't get answer from ajax call
                private_methods.errMsg("result_wizard: no response from ajax call");
              } else if ('status' in response) {
                switch (response.status) {
                  case "ok":
                    // Make the HTML response visible in a 'result_container_{num}'
                    $(sTargetId).html(response.html);
                    // Make sure events are set again
                    ru.cesar.seeker.init_events();
                    break;
                  case "error":
                    // Indicate there is an error
                    private_methods.errMsg("Response contains an error");
                    // Make the HTML response visible in a 'result_container_{num}'
                    $(sTargetId).html(response.html);
                    // Make sure events are set again
                    ru.cesar.seeker.init_events();
                    break;
                  default:
                    // Indicate there is an error
                    private_methods.errMsg("result_wizard: Unknown status: "+response.status);
                    break;
                }
              } else {
                // There is no status in the response
                private_methods.errMsg("result_wizard: no status in response from ajax call");
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
            case "6":
              // Show the hierarchical table in the appropriate location
              oTree = JSON.parse(response.sent_info.allT);
              crpstudio.htable.treeToHtable("#sentdetails_htable", oTree, "#sentdetails_err");
              break;
          }
          $("#result_wait_message").addClass("hidden");


        } catch (ex) {
          private_methods.errMsg("result_wizard", ex);
        }
      },

      /**
       * treeToHtable
       *    Convert the object tree into a Htable
       *
       */
      treeToHtable: function (divHtable, oTree, divErr) {
        try {

        } catch (ex) {
          private_methods.errMsg("treeToHtable", ex);
        }
      },

      /**
       * research_wizard
       *    Select one item from the research project wizard
       *
       */
      research_wizard: function (el, sPart, bOnlyOpen, clstarget, sSelect) {
        var sTargetId = "research_container_",
            sContainerId = "research_container_",
            sTargetType = "",
            sObjectId = "",
            sMsg = "",
            html = "",
            sUrl = "",
            data = {},
            frm = null,
            th = null,
            response = null,
            elWait = null,      // Div that should be opened/closed to indicate waiting
            elListItem = null,
            elList = null;

        try {
          // Set waiting div
          elWait = private_methods.waitInit(el);
          // Start waiting
          private_methods.waitStart(elWait);

          // If this comes from the main dashboard, show waiting over there
          private_methods.mainWaitStart();
          
          // Get the correct target id
          if (clstarget !== undefined && clstarget !== "") {
            // Look for the nearest container
            sContainerId = "#" + $(el).closest(".research-part").first().attr("id");
            // Use [clstarget] for my own targetid: but only within the container
            sTargetId = sContainerId + " ." + clstarget;
          } else {
            sTargetId = "#" + sTargetId + sPart;
            sContainerId = sTargetId;
          }
          sObjectId = $("#researchid").text().trim();

          // Do we need to indicate selection?
          if (sSelect !== undefined && sSelect === "select") {
            // First deselect all <th> elements
            $(el).closest(".research-part").find("th").removeClass("selected");
            // Clear what we had
            $(sTargetId).html("");
            // Indicate that the <th> above is selected
            th = $(el).closest("th");
            if (th !== null) {
              $(th).addClass("selected");
            }
          }

          if (bOnlyOpen === undefined || bOnlyOpen === false) {
            sTargetType = $("#id_research-targetType").val();
            // If it is undefined, try to get the target type from the input
            if (sTargetType === undefined || sTargetType === "") {
              sTargetType = $("#targettype").text().trim();
              if (sTargetType === "") {
                sTargetType = "w";  // Take words as default
              }
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
                  // If this comes from the main dashboard, show waiting over there
                  private_methods.mainWaitStop();
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
              case "72": if (sMsg === "") sMsg = "7-before-72";
              case "73": if (sMsg === "") sMsg = "72-before-73";
                // Opening a new form requires prior processing of the current form
                if (frm !== undefined) {
                  data = $(frm).serializeArray();
                  var button = $(frm).find(".submit-row .ajaxform");
                  if (button !== undefined) {
                    // Indicate we are saving
                    $(".save-warning").html("Processing... " + sMsg + loc_sWaiting);
                    data.push({ 'name': 'instanceid', 'value': $(button).attr("instanceid") });
                    // Determine the URL
                    sUrl = $(button).attr("ajaxurl");
                    // Process this information: save the data!
                    response = ru.cesar.seeker.ajaxcall(sUrl, data, "POST");
                    // Check the response
                    if (response.status === undefined || response.status !== "ok") {
                      // Action to undertake if we have not been successfull
                      private_methods.errMsg("research_wizard[" + sPart + "]: could not save the data for this function");
                      // Stop waiting
                      private_methods.waitStop(elWait);
                      // If this comes from the main dashboard, show waiting over there
                      private_methods.mainWaitStop();
                      // And leave...
                      return;
                    }
                  }
                }
                break;
            }
            switch (sPart) {
              case "62":
                // If a new condition has been created, then this is where we expect the instance number to appear
                if ('cond_instanceid' in response) {
                  $(el).attr("instanceid", response['cond_instanceid']);
                }
                break;
              case "72":
                // If a new feature has been created, then this is where we expect the instance number to appear
                if ('feat_instanceid' in response) {
                  $(el).attr("instanceid", response['feat_instanceid']);
                }
                break;
            }
          }

          // [2] Load the new form through an AJAX call
          data = [];
          switch (sPart) {
            case "1": case "2": case "3":
            case "4": case "42": case "43": case "44":
            case "6": case "62": case "63":
            case "7": case "72": case "73":
            case "8":

              // CHeck if we need to take another instance id instead of #researchid
              if ($(el).attr("instanceid") !== undefined) { sObjectId = $(el).attr("instanceid"); }
              // Indicate we are saving/preparing
              $(".save-warning").html("Processing... " + sPart + loc_sWaiting);
              // Determine the URL
              sUrl = $(el).attr("ajaxurl");
              if (sUrl === undefined) {
                sUrl = $(el).attr("targeturl");
              }
              // Fetch the corr
              response = ru.cesar.seeker.ajaxform_load(sUrl, sObjectId, data);
              if (response.status && response.status === "ok") {
                // Make the HTML response visible
                $(sTargetId).html(response.html);
                // Make sure events are set again
                ru.cesar.seeker.init_events();
                // Disable the save warning
                $(".save-warning").html("");
              }
              break;
          }
          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);

          // Some actions depend on the particular page we are going to visit
          switch (sPart) {
            case "4": case "42":
              // add any event handlers for wizard part '42'
              ru.cesar.seeker.init_cvar_events();
              break;
            case "43": case "44":
            case "62": case "63":
            case "72": case "73":
            case "8": 
              // add any event handlers for wizard part '43' and part '44'
              // As well as for '62' and '63'
              ru.cesar.seeker.init_arg_events();
              break;
            case "6":
              // add any event handlers for wizard part '6'
              ru.cesar.seeker.init_cond_events();
              break;
            case "7":
              // add any event handlers for wizard part '7'
              ru.cesar.seeker.init_feat_events();
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

          // $(sTargetId).removeClass("hidden");
          $(sContainerId).removeClass("hidden");
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
              $("#goto_overview").removeClass("hidden");
              $("#goto_finetune").addClass("hidden");
              /* OLD code 
              $("#goto_overview").addClass("hidden");
              $("#goto_finetune").removeClass("hidden");
              */
              break;
          }
          // Stop waiting
          private_methods.waitStop(elWait);
          // If this comes from the main dashboard, show waiting over there
          private_methods.mainWaitStop();
        } catch (ex) {
          private_methods.errMsg("research_wizard", ex);
          // Stop waiting
          private_methods.waitStop(elWait);
        }
      },
      /**
      * main_info_hide
      *    Behaviour when there is a mouse-out on a main blob
      * 
      * @param {element} elRect
      * @returns {undefined}
      */
      main_info_hide: function (elRect) {
        try {
          $("#main_info_div").addClass("hidden");
        } catch (ex) {
          // Show the error at the indicated place
          private_methods.errMsg("main_info_hide error: ", ex);
        }
      },
      /**
      * main_info_show
      *    Behaviour when there is a mouse-over on a main blob
      * 
      * @param {element} elRect
      * @returns {undefined}
      */
      main_info_show: function (elRect) {
        var sPart,        // Counter
            i,            // Counter
            sInfoDiv = "#main_info_div",
            sInfo = "",
            lInfo = [],
            lHtml = [],   // Where we gather HTML
            oSvg,         // Coordinates of the svg rect element
            elTarget,     // The <div> we want to position
            oFeat = {},   // Feature object
            sId = "";     // Identifier of the element that has been hit

        try {
          // Validate: this must be a <g> element with class ".main-el"
          if (!$(elRect).is("g.main-el")) {
            return;
          }
          // The node must have an identifier
          sId = $(elRect).attr("id");
          // The text to be shown is in the @info attribute of the <g> element
          sInfo = $(elRect).attr("info");
          if (sInfo !== undefined && sInfo !== "") {
            // There is some text to be shown
            lInfo = sInfo.split("\\n");
            lHtml.push("<div id='info-" + sId + "' class='svg-main'><table>");
            for (i = 0; i < lInfo.length; i++) {
              sPart = lInfo[i];
              lHtml.push("<tr><td class='cellvalue'>" + sPart + "</td></tr>");
            }
            lHtml.push("</table></div>");

            // Add this element at an appropriate place
            $(sInfoDiv).html(lHtml.join("\n"));
            elTarget = $(sInfoDiv).find(".svg-main").get(0);

            // Get screen coordinates
            oSvg = private_methods.screenCoordsForRect($(elRect).children("rect").first());
            elTarget.style.left = oSvg['x'] + 'px';
            elTarget.style.top = (oSvg['y'] - 10 - 20 * lInfo.length).toString() + 'px';
            $(sInfoDiv).removeClass("hidden");

            /*
            // Now adjust the position based on the shown div
            oSvg = private_methods.fitFeatureBox(oSvg, elTarget);
            elTarget.style.left = oSvg['x'] + 'px';
            elTarget.style.top = oSvg['y'] + 'px';
            */
          }

        } catch (ex) {
          // Show the error at the indicated place
          private_methods.errMsg("main_info_show error: ", ex);
        }
      },

      /**
      * result_qsubinfo
      *    Open the following <tr> and KWIC-show [qsubinfo_id]
      * 
      * @param {element} elThis
      * @param {string} qsubinfo_id
      * @returns {void}
      */
      result_qsubinfo: function (elThis, qsubinfo_id) {
        var elTr = null,
            elWait = null,
            frm = null,
            data = null,
            ajaxurl = null,
            elTd = null;

        try {
          // Clear previous errors
          private_methods.errClear();
          // Set waiting div
          elWait = private_methods.waitInit(elThis);
          // Start waiting
          private_methods.waitStart(elWait);
          // Get the element we are looking for
          elTr = $(elThis).next("tr");
          // Are we opening or closing?
          if ($(elTr).hasClass("hidden")) {
            // We are trying to open and show
            // Hide all [.qsubinfo-show] items
            $(elThis).closest("tbody").find(".qsubinfo-show").addClass("hidden");
            // Show contents
            $(elTr).removeClass("hidden");
            elTd = $(elTr).children("td").first();
            $(elTd).html("<span><i>looking for the data...</i></span><span class=\"glyphicon glyphicon-refresh glyphicon-refresh-animate\"></span>");
            
            // Gather the information
            frm = $("#qc_form");
            if (frm !== undefined) { data = $(frm).serializeArray(); }

            // Ask for the required information
            ajaxurl = $(elThis).attr("ajaxurl");
            $.post(ajaxurl, data, function (response) {
              if (response.status === undefined) {
                // Show an error somewhere
                private_methods.errMsg("Bad qsubinfo response");
              } else if (response.status === "error") {
                // Show the error that has occurred
                if ("html" in response) { sMsg = response['html']; }
                if ("error_list" in response) { sMsg += response['error_list']; }
                private_methods.errMsg("Qsubinfo error: " + sMsg);
              } else {
                // Everything is in order: recover and show the data
                if ("html" in response) {
                  var sHtml = response["html"];
                  $(elTd).html(sHtml);
                }
              }
            });

          } else {
            // Need to close
            $(elTr).addClass("hidden");
          }

          // Stop waiting
          private_methods.waitStop(elWait);
        } catch (ex) {
          private_methods.errMsg("result_qsubinfo", ex);
          // Stop waiting
          private_methods.waitStop(elWait);
        }
      },
      /**
       * search_download
       *   Trigger creating and downloading the CRPX
       *
       */
      search_download: function (elStart) {
        var ajaxurl = "",
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
          // Set the 'action; attribute in the form
          frm.attr("action", ajaxurl);
          frm.submit();

        } catch (ex) {
          private_methods.errMsg("search_download", ex);
        }
      },

      /**
       * jumpto_item
       *   Jump to the indicated item
       *
       */
      jumpto_item: function (el) {
        var inst_type = "", // Instance type
            sPart = "",
            sUrl = "";      // URL to jump to

        try {
          if (el !== undefined) {
            inst_type = $(el).attr("jumptype");
            sUrl = $(el).attr("ajaxurl");
            if (inst_type !== undefined && inst_type !== "" && 
                sUrl !== undefined && sUrl !== "") {
              switch (inst_type) {
                case "cvar": sPart = "43"; break;
                case "cond": sPart = "62"; break;
                case "feat": sPart = "72"; break;
              }
              if (sPart !== "") {
                // Ask the wizard to open appropriately
                ru.cesar.seeker.research_wizard(el, sPart, true);
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("jumpto_item", ex);
        }
      },

      /**
       * result_download
       *   Trigger creating and downloading a result CSV
       *
       */
      post_download: function (elStart) {
        var ajaxurl = "",
            contentid = null,
            response = null,
            basket_id = -1,
            scaleFactor = 4,  // Scaling of images to make sure the result is not blurry
            frm = null,
            el = null,
            sHtml = "",
            oBack = null,
            dtype = "",
            resid="",
            sMsg = "",
            getCanvas,
            data = [];

        try {
          // Clear the errors
          private_methods.errClear();

          // obligatory parameter: ajaxurl
          ajaxurl = $(elStart).attr("ajaxurl");
          contentid = $(elStart).attr("contentid");

          // Gather the information
          frm = $(elStart).closest(".container-small").find("form");
          if (frm.length === 0) {
            frm = $(elStart).closest(".container.body-content").find("form");
            if (frm.length === 0) {
              frm = $(elStart).closest(".container-large.body-content").find("form");
            }
          }
          // Set the 'action; attribute in the form
          frm.attr("action", ajaxurl);
          // Make sure we do a POST
          frm.attr("method", "POST");

          // Get the download type and put it in the <input>
          dtype = $(elStart).attr("downloadtype");
          $(frm).find("#downloadtype").val(dtype);

          resid = $(elStart).attr("resid");
          if (resid !== undefined && resid != "") {
            $(frm).find("#resid").val(resid);
          }

          // Do we have a contentid?
          if (contentid !== undefined && contentid !== null && contentid !== "") {
            // Process download data
            switch (dtype) {
              case "tree":
                sHtml = private_methods.prepend_styles(contentid, "svg");
                // Set it
                $(frm).find("#downloaddata").val(sHtml);
                // Now submit the form
                oBack = frm.submit();
                break;
              case "htable":
                // Prepend any styles
                sHtml = private_methods.prepend_styles(contentid, "html");
                // Set it
                $(frm).find("#downloaddata").val(sHtml);
                // Now submit the form
                oBack = frm.submit();
                break;
              case "htable-png":
                // Make sure we get the table
                contentid = contentid + " table";
              case "tree-png":
                // Make sure we only get SVG
                if (dtype === "tree-png") {
                  // contentid = contentid + " svg";
                }
                // Convert html to canvas
                el = $(contentid).first().get(0);

                html2canvas(el, { scale: scaleFactor })
                  .then(function (canvas) {
                    // Convert to data
                    var imageData = canvas.toDataURL("image/png");
                    $(frm).find("#downloaddata").val(imageData);
                    // Now submit the form
                    oBack = frm.submit();
                });
                break;
              default:
                // TODO: add error message here
                return;
            }
          }

          // Check on what has been returned
          if (oBack !== null) {

          }
        } catch (ex) {
          private_methods.errMsg("post_download", ex);
        }
      },

      /**
       * search_start
       *   Check and then start a search
       *   Note: returning from the $.post call only means
       *         that a BASKET object has been created...
       *
       */
      search_start(elStart) {
        var sDivProgress = "#research_progress",
            ajaxurl = "",
            butWatch = null,  // The button that contains the in progress
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

          // Make an ASYNCHRONOUS ajax call to START OFF the search
          $.post(ajaxurl, data, function (response) {
            if (response.status === undefined) {
              // Show an error somewhere
              private_methods.errMsg("Bad execute response");
              $(sDivProgress).html("Bad execute response:<br>" + response);
            } else if (response.status === "error") {
              // Show the error that has occurred
              if ("html" in response) { sMsg = response['html']; }
              if ("error_list" in response) { sMsg += response['error_list']; }
              private_methods.errMsg("Execute error: " + sMsg);
              $(sDivProgress).html("execution error");
            } else {
              // All went well -- get the basket id
              basket_id = response.basket_id;
              basket_start = response.basket_start;
              basket_progress = response.basket_progress;
              basket_stop = response.basket_stop;
              basket_watch = response.basket_watch;
              basket_result = response.basket_result;
              basket_data = data;

              // Make the watch (=InProgress) button available
              butWatch = $("#action_inprogress").find("button").first();
              $(butWatch).attr("ajaxurl", basket_watch);
              $(butWatch).attr("basket_id", basket_id);
              $(butWatch).attr("part_id", $("#select_part").val());
              $("#action_inprogress").removeClass("hidden");

              // Make the stop button available
              $("#research_stop").removeClass("hidden");
              $(sDivProgress).html("Conversion to Xquery...");
              // Disable the START button
              $("#research_start").prop("disabled", true);

              // Start the next call for status after 2 seconds
              setTimeout(function () { ru.cesar.seeker.search_progress(); }, 500);

              // Now make sure that the Translation + Execution starts
              $.post(basket_start, data, function (response) {
                // Interpret the response that is returned
                if (response.status === undefined) {
                  // Show an error somewhere
                  private_methods.errMsg("Basket-start response status undefined");
                  $(sDivProgress).html("Bad execute response:<br>" + response);
                  $("#action_inprogress").addClass("hidden");
                } else if (response.status === "error") {
                  // Show the error that has occurred
                  if ("html" in response) { sMsg = response['html']; }
                  if ("error_list" in response) { sMsg += response['error_list']; }
                  // Show that the project has finished
                  if ("html" in response) {
                    $(sDivProgress).html(response.html);
                  } else {
                    private_methods.errMsg("Execute error: " + sMsg);
                    $(sDivProgress).html("execution error (see above)");
                  }
                  $("#action_inprogress").addClass("hidden");
                } else {
                  // All went well, and the search has finished
                  // No further action is needed
                }
                // Re-enable the START button in all cases
                $("#research_start").prop("disabled", false);
              });
            }
          });

        } catch (ex) {
          private_methods.errMsg("search_start", ex);
        }
      },
      
      /**
       * search_stop
       *   Stop an already going search
       *
       */
      search_stop(el) {
        var sDivProgress = "#research_progress",
            response = null;
        try {
          // Enable the START button
          $("#research_start").prop("disabled", false);
          // Hide the in progress button
          $("#action_inprogress").addClass("hidden");
          // Make an AJAX call by using the already stored basket_stop URL
          $.post(basket_stop, basket_data, function (response) {
            if (response.status !== undefined) {
              switch (response.status) {
                case "ok":
                  $(sDivProgress).html("Stopped gracefully");
                  break;
                case "error":
                  $(sDivProgress).html("Stopped with an error");
                  break;
              }
            }
          });

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
          // response = ru.cesar.seeker.ajaxcall(basket_progress, basket_data, "POST");
          $.post(basket_progress, basket_data, function (response) {
            if (response.status !== undefined) {
              if ('html' in response) { sMsg = response.html; }
              switch (response.status) {
                case "ok":
                  // Action depends on the statuscode
                  switch (response.statuscode) {
                    case "working":
                    case "preparing":
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
                      // Allow starting again
                      $("#research_start").prop("disabled", false);
                      // Show the RESULTS button
                      $("#research_results").removeClass("hidden");
                      // Set the correct href for the button
                      $("#research_results").attr("href", basket_result);
                      // Hide the IN-PROGRESS button
                      $("#action_inprogress").addClass("hidden");
                      break;
                    case "error":
                      // THis is an Xquery error
                      // Show that the project has finished
                      $(sDivProgress).html("Sorry, but there is an error");
                      // Hide the STOP button
                      $("#research_stop").addClass("hidden");
                      // Do NOT shoe the RESULTS button
                      // Hide the IN-PROGRESS button
                      $("#action_inprogress").addClass("hidden");
                      break;
                    case "stop":
                      // Stop asking for progress
                      // Hide the STOP button
                      $("#research_stop").addClass("hidden");
                      // Hide the IN-PROGRESS button
                      $("#action_inprogress").addClass("hidden");
                      break;
                    default:
                      if (response.statuscode !== "") {
                        // Show the current status
                        private_methods.errMsg("Unknown statuscode: [" + response.statuscode + "]");
                      }
                      // We continue anyway, because this is not an error
                      setTimeout(function () { ru.cesar.seeker.search_progress(); }, 500);
                      break;
                  }
                  break;
                case "error":
                  if ('error_list' in response) { sMsg += response.error_list; }
                  private_methods.errMsg("Progress error: " + sMsg);
                  // Hide the IN-PROGRESS button
                  $("#action_inprogress").addClass("hidden");
                  break;
                case "stop":
                  // Hide the IN-PROGRESS button
                  $("#action_inprogress").addClass("hidden");
                  // No further action is needed unless there is a message??
                  break;
              }
            }
          });

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
            data.push({ 'name': '_task', 'value': sTask });
            switch (sTask) {
              case "copy_cvar_function":
                data.push({ 'name': '_functionid', 'value': function_id });
                data.push({ 'name': '_constructionid', 'value': $(divTarget).val() });
                break;
              case "copy_condition_function":
                data.push({ 'name': '_functionid', 'value': function_id });
                data.push({ 'name': '_conditionid', 'value': $(divTarget).val() });
                break;
              case "copy_feature_function":
                data.push({ 'name': '_functionid', 'value': function_id });
                data.push({ 'name': '_featureid', 'value': $(divTarget).val() });
                break;
            }
            // Find out where the save button is located
            divSave = $(elThis).closest("form").find(".submit-row button").first();
            if (divSave !== null) {
              // Position the data in place
              $(divSave).attr("extra", JSON.stringify( data));
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
            elTr = $(elTr).nextAll(".part-del").first();
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
       * toggle_click
       *   Action when user clicks an element that requires toggling a target
       *
       */
      toggle_click: function (elThis) {
        var elGroup = null,
            elTarget = null,
            sStatus = "";

        try {
          // Get the target to be opened
          elTarget = $(elThis).attr("targetid");
          // Sanity check
          if (elTarget !== null) {
            // Show it if needed
            if ($("#"+elTarget).hasClass("hidden")) {
              $("#" + elTarget).removeClass("hidden");
            } else {
              $("#" + elTarget).addClass("hidden");
            }
          }
        } catch (ex) {
          private_methods.errMsg("toggle_click", ex);
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

