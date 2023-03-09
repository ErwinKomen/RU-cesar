var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

(function ($) {
  $(function () {
    $(document).ready(function () {
      // Initialize event listeners
      ru.basic.init_events();
      // ru.basic.init_typeahead();

      // Initialize Bootstrap popover
      // Note: this is used when hovering over the question mark button
      $('[data-toggle="popover"]').popover();
    });
  });
})(django.jQuery);



// based on the type, action will be loaded

// var $ = django.jQuery.noConflict();

var ru = (function ($, ru) {
  "use strict";

  ru.basic = (function ($, config) {
    // Define variables for ru.basic here
    var loc_divErr = "basic_err",
        loc_urlStore = "",      // Keep track of URL to be shown
        loc_progr = [],         // Progress tracking
        loc_sWaiting = " <span class=\"glyphicon glyphicon-refresh glyphicon-refresh-animate\"></span>",
        loc_bManuSaved = false,
        KEYS = {
          BACKSPACE: 8, TAB: 9, ENTER: 13, SHIFT: 16, CTRL: 17, ALT: 18, ESC: 27, SPACE: 32, PAGE_UP: 33, PAGE_DOWN: 34,
          END: 35, HOME: 36, LEFT: 37, UP: 38, RIGHT: 39, DOWN: 40, DELETE: 46
        },
        dummy = 1;

    // Private methods specification
    var private_methods = {
      /**
       * aaaaaaNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      aaaaaaNotVisibleFromOutside: function () {
        return "something";
      },

      /** 
       *  errClear - clear the error <div>
       */
      errClear: function () {
        $("#" + loc_divErr).html("");
      },

      /** 
       *  errMsg - show error message in <div> loc_divErr
       */
      errMsg: function (sMsg, ex) {
        var sHtml = "Error in [" + sMsg + "]<br>";
        if (ex !== undefined && ex !== null) {
          sHtml = sHtml + ex.message;
        }
        $("#" + loc_divErr).html(sHtml);
      },

      /** 
       *  waitInit - initialize waiting
       */
      waitInit: function (el) {
        var elWaith = null;

        try {
          // Right now no initialization is defined
          return elWait;
        } catch (ex) {
          private_methods.errMsg("waitInit", ex);
        }
      },

      /** 
       *  waitStart - Start waiting by removing 'hidden' from the DOM point
       */
      waitStart: function (el) {
        if (el !== null) {
          $(el).removeClass("hidden");
        }
      },

      /** 
       *  waitStop - Stop waiting by adding 'hidden' to the DOM point
       */
      waitStop: function (el) {
        if (el !== null) {
          $(el).addClass("hidden");
        }
      }
    }
    // Public methods
    return {
      /**
       * add_new_select2
       *    Show [table_new] element
       *
       */
      add_new_select2: function (el, prefix, template_selection) {
        var elTr = null,
            elRow = null,
            options = {},
            elDiv = null;

        try {
          elTr = $(el).closest("tr");           // Nearest <tr>
          elDiv = $(elTr).find(".new-mode");    // The div with new-mode in it
          // Show it
          $(elDiv).removeClass("hidden");
          // Find the first row
          elRow = $(elDiv).find("tbody tr").first();
          options['select2'] = true;
          options['prefix'] = prefix;
          options['table'] = prefix + "_formset";
          options['events'] = ru.basic.init_typeahead;
          options['counter'] = false;
          if (template_selection !== undefined) {
            options['select2_options'] = { "templateSelection": template_selection }
          }
          ru.basic.tabular_addrow($(elRow), options);

          // Add
        } catch (ex) {
          private_methods.errMsg("add_new_select2", ex);
        }
      },

      /**
       * check_progress
       *    Check the progress of reading e.g. codices
       *
       */
      check_progress: function (progrurl, sTargetDiv) {
        var elTarget = "#" + sTargetDiv,
            sMsg = "",
            lHtml = [];

        try {
          $(elTarget).removeClass("hidden");
          // Call the URL
          $.get(progrurl, function (response) {
            // Action depends on the response
            if (response === undefined || response === null || response.status === undefined) {
              private_methods.errMsg("No status returned");
            } else {
              switch (response.status) {
                case "ready":
                case "finished":
                  // NO NEED for further action
                  //// Indicate we are ready
                  //$(elTarget).html("READY");
                  break;
                case "error":
                  // Show the error
                  if (response.msg !== undefined) {
                    $(elTarget).html(response.msg);
                  } else {
                    $(elTarget).html("An error has occurred (basic check_progress)");
                  }
                  break;
                default:
                  if (response.msg !== undefined) { sMsg = response.msg; }
                  // Combine the status
                  sMsg = "<tr><td>" + response.status + "</td><td>" + sMsg + "</td></tr>";
                  // Check if it is on the stack already
                  if ($.inArray(sMsg, loc_progr) < 0) {
                    loc_progr.push(sMsg);
                  }
                  // Combine the status HTML
                  sMsg = "<div style=\"max-height: 200px; overflow-y: scroll;\"><table>" + loc_progr.reverse().join("\n") + "</table></div>";
                  $(elTarget).html(sMsg);
                  // Make sure we check again
                  window.setTimeout(function () { ru.basic.check_progress(progrurl, sTargetDiv); }, 200);
                  break;
              }
            }
          });

        } catch (ex) {
          private_methods.errMsg("check_progress", ex);
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
        var elTotalForms = null,
            total = 0;

        try {
          // Clone the element in [selector]
          var newElement = $(selector).clone(true);
          // Find the total number of [type] elements
          elTotalForms = $('#id_' + type + '-TOTAL_FORMS').first();
          // Determine the total of already available forms
          if (elTotalForms === null || elTotalForms.length === 0) {
            // There is no TOTAL_FORMS for this type, so calculate myself
          } else {
            // Just copy the TOTAL_FORMS value
            total = parseInt($(elTotalForms).val(), 10);
          }

          // Find each <input> element
          newElement.find(':input').each(function (idx, el) {
            var name = "",
                id = "",
                val = "",
                td = null;

            if ($(el).attr("name") !== undefined) {
              // Get the name of this element, adapting it on the fly
              name = $(el).attr("name").replace("__prefix__", total.toString());
              // Produce a new id for this element
              id = $(el).attr("id").replace("__prefix__", total.toString());
              // Adapt this element's name and id, unchecking it
              $(el).attr({ 'name': name, 'id': id }).val('').removeAttr('checked');
              // Possibly set a default value
              td = $(el).parent('td');
              if (td.length === 0) {
                td = $(el).parent("div").parent("td");
              }
              if (td.length === 1) {
                val = $(td).attr("defaultvalue");
                if (val !== undefined && val !== "") {
                  $(el).val(val);
                }
              }
            }
          });
          newElement.find('select').each(function (idx, el) {
            var td = null;

            if ($(el).attr("name") !== undefined) {
              td = $(el).parent('td');
              if (td.length === 0) { td = $(el).parent("div").parent("td"); }
              if (td.length === 0 || (td.length === 1 && $(td).attr("defaultvalue") === undefined)) {
                // Get the name of this element, adapting it on the fly
                var name = $(el).attr("name").replace("__prefix__", total.toString());
                // Produce a new id for this element
                var id = $(el).attr("id").replace("__prefix__", total.toString());
                // Adapt this element's name and id, unchecking it
                $(el).attr({ 'name': name, 'id': id }).val('').removeAttr('checked');
              }
            }
          });

          // Find each <label> under newElement
          newElement.find('label').each(function (idx, el) {
            if ($(el).attr("for") !== undefined) {
              // Adapt the 'for' attribute
              var newFor = $(el).attr("for").replace("__prefix__", total.toString());
              $(el).attr('for', newFor);
            }
          });

          // Look at the inner text of <td>
          newElement.find('td').each(function (idx, el) {
            var elInsideTd = $(el).find("td");
            var elText = $(el).children().first();
            if (elInsideTd.length === 0 && elText !== undefined) {
              var sHtml = $(elText).html();
              if (sHtml !== undefined && sHtml !== "") {
                sHtml = sHtml.replace("__counter__", (total + 1).toString());
                $(elText).html(sHtml);
              }
              // $(elText).html($(elText).html().replace("__counter__", total.toString()));
            }
          });
          // Look at the attributes of <a> and of <input>
          newElement.find('a, input').each(function (idx, el) {
            // Iterate over all attributes
            var elA = el;
            $.each(elA.attributes, function (i, attrib) {
              var attrText = $(elA).attr(attrib.name).replace("__counter__", total.toString());
              // EK (20/feb): $(this).attr(attrib.name, attrText);
              $(elA).attr(attrib.name, attrText);
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
            $(selector).closest("tbody").children("tr.form-row").not(".empty-form").each(function (idx, el) {
              var elFirstCell = $(el).find("td").not(".hidden").first();
              $(elFirstCell).html(iRow);
              iRow += 1;
            });
          }

          // Return the new <tr> 
          return newElement;

        } catch (ex) {
          private_methods.errMsg("cloneMore", ex);
          return null;
        }
      },

      /**
       * delete_cancel
       *   Hide this <tr> and cancel the delete
       *
       */
      delete_cancel: function (el) {
        try {
          $(el).closest("div.delete-confirm").addClass("hidden");
        } catch (ex) {
          private_methods.errMsg("delete_cancel", ex);
        }
      },

      /**
       * delete_confirm
       *   Open the next <tr> to get delete confirmation (or not)
       *
       */
      delete_confirm: function (el, bNeedConfirm) {
        var elDiv = null;

        try {
          if (bNeedConfirm === undefined) { bNeedConfirm = true; }
          // Action depends on the need for confirmation
          if (bNeedConfirm) {
            // Find the [.delete-row] to be shown
            elDiv = $(el).closest("tr, .panel").find(".delete-confirm").first();
            if (elDiv.length === 0) {
              // Try goint to the next <tr>
              elDiv = $(el).closest("tr, .panel").next("tr.delete-confirm");
            }
            $(elDiv).removeClass("hidden");
          } else {

          }
        } catch (ex) {
          private_methods.errMsg("delete_confirm", ex);
        }
      },

      /**
       * filter_click
       *    What happens when clicking a badge filter
       *
       */
      filter_click: function (el) {
        var target = null,
            specs = null;

        try {
          target = $(this).attr("targetid");
          if (target !== undefined && target !== null && target !== "") {
            target = $("#" + target);
            // Action depends on checking or not
            if ($(this).hasClass("on")) {
              // it is on, switch it off
              $(this).removeClass("on");
              $(this).removeClass("jumbo-3");
              $(this).addClass("jumbo-1");
              // Must hide it and reset target
              $(target).addClass("hidden");

              // Check if target has a targetid
              specs = $(target).attr("targetid");
              if (specs !== undefined && specs !== "") {
                // Reset related badges
                $(target).find("span.badge").each(function (idx, elThis) {
                  var subtarget = "";

                  $(elThis).removeClass("on");
                  $(elThis).removeClass("jumbo-3");
                  $(elThis).removeClass("jumbo-2");
                  $(elThis).addClass("jumbo-1");
                  subtarget = $(elThis).attr("targetid");
                  if (subtarget !== undefined && subtarget !== "") {
                    $("#" + subtarget).addClass("hidden");
                  }
                });
                // Re-define the target
                target = $("#" + specs);
              }

              $(target).find("input").each(function (idx, elThis) {
                $(elThis).val("");
              });
              // Also reset all select 2 items
              $(target).find("select").each(function (idx, elThis) {
                $(elThis).val("").trigger("change");
              });

            } else {
              // Must show target
              $(target).removeClass("hidden");
              // it is off, switch it on
              $(this).addClass("on");
              $(this).removeClass("jumbo-1");
              $(this).addClass("jumbo-3");
            }

          }
        } catch (ex) {
          private_methods.errMsg("filter_click", ex);
        }
      },

      /**
       * goto_url
       *   Go to the indicated target URL
       *
       */
      goto_url: function (target) {
        try {
          location.href = target;
        } catch (ex) {
          private_methods.errMsg("goto_url", ex);
        }
      },

      /**
       * import_data
       *   Allow user to upload a file
       *
       * Assumptions:
       * - the [el] contains parameter  @targeturl
       * - there is a div 'import_progress'
       * - there is a div 'id_{{ftype}}-{{forloop.counter0}}-file_source'
       *   or one for multiple files: 'id_files_field'
       *
       */
      import_data: function (sKey) {
        var frm = null,
            targeturl = "",
            options = {},
            fdata = null,
            el = null,
            elProg = null,    // Progress div
            elErr = null,     // Error div
            progrurl = null,  // Any progress function to be called
            data = null,
            xhr = null,
            files = null,
            sFtype = "",      // Type of function (cvar, feat, cond)
            elWait = null,
            bDoLoad = false,  // Need to load with a $.get() afterwards
            elInput = null,   // The <input> element with the files
            more = {},        // Additional (json) data to be passed on (from form-data)
            sTargetDiv = "",  // The div where the uploaded reaction comes
            sSaveDiv = "",    // Where to go if saving is needed
            sMsg = "";

        try {
          // The element to use is the key + import_info
          el = $("#" + sKey + "-import_info");
          elProg = $("#" + sKey + "-import_progress");
          elErr = $("#" + sKey + "-import_error");

          // Set the <div> to be used for waiting
          elWait = private_methods.waitInit(el);

          // Get the URL
          targeturl = $(el).attr("targeturl");
          progrurl = $(el).attr("sync-progress");
          sTargetDiv = $(el).attr("targetid");
          sSaveDiv = $(el).attr("saveid");

          if (targeturl === undefined && sSaveDiv !== undefined && sSaveDiv !== "") {
            targeturl = $("#" + sSaveDiv).attr("ajaxurl");
            sTargetDiv = $("#" + sSaveDiv).attr("openid");
            sFtype = $(el).attr("ftype");
            bDoLoad = true;
          }

          if ($(el).is("input")) {
            elInput = el;
          } else {
            elInput = $(el).find("input").first();
          }

          // Show progress
          $(elProg).attr("value", "0");
          $(elProg).removeClass("hidden");
          if (bDoLoad) {
            $(".save-warning").html("loading the definition..." + loc_sWaiting);
            $(".submit-row button").prop("disabled", true);
          }

          // Add data from the <form> nearest to me: 
          frm = $(el).closest("form");
          if (frm !== undefined) { data = $(frm).serializeArray(); }

          for (var i = 0; i < data.length; i++) {
            more[data[i]['name']] = data[i]['value'];
          }
          // Showe the user needs to wait...
          private_methods.waitStart(elWait);

          // Now initiate any possible progress calling
          if (progrurl !== null) {
            loc_progr = [];
            window.setTimeout(function () { ru.basic.check_progress(progrurl, sTargetDiv); }, 2000);
          }

          // Upload XHR
          $(elInput).upload(targeturl,
            more,
            function (response) {
              // Transactions have been uploaded...
              console.log("done: ", response);

              // Show where we are
              $(el).addClass("hidden");
              $(".save-warning").html("saving..." + loc_sWaiting);

              // First leg has been done
              if (response === undefined || response === null || response.status === undefined) {
                private_methods.errMsg("No status returned");
              } else {
                switch (response.status) {
                  case "ok":
                    // Check how we should react now
                    if (bDoLoad) {
                      // Show where we are
                      $(".save-warning").html("retrieving..." + loc_sWaiting);

                      $.get(targeturl, function (response) {
                        if (response === undefined || response === null || response.status === undefined) {
                          private_methods.errMsg("No status returned");
                        } else {
                          switch (response.status) {
                            case "ok":
                              // Show the response in the appropriate location
                              $("#" + sTargetDiv).html(response.html);
                              $("#" + sTargetDiv).removeClass("hidden");
                              break;
                            default:
                              // Check how/what to show
                              if (response.err_view !== undefined) {
                                private_methods.errMsg(response['err_view']);
                              } else if (response.error_list !== undefined) {
                                private_methods.errMsg(response['error_list']);
                              } else {
                                // Just show the HTML
                                $("#" + sTargetDiv).html(response.html);
                                $("#" + sTargetDiv).removeClass("hidden");
                              }
                              break;
                          }
                          // Make sure events are in place again
                          ru.basic.init_events();
                          switch (sFtype) {
                            case "cvar":
                              ru.basic.init_cvar_events();
                              break;
                            case "cond":
                              ru.basic.init_cond_events();
                              break;
                            case "feat":
                              ru.basic.init_feat_events();
                              break;
                          }
                          // Indicate we are through with waiting
                          private_methods.waitStop(elWait);
                        }
                      });
                    } else {
                      // Remove all project-part class items
                      $(".project-part").addClass("hidden");
                      $(".save-warning").html("");
                      // Place the response here
                      $("#" + sTargetDiv).html(response.html);
                      $("#" + sTargetDiv).removeClass("hidden");
                    }
                    break;
                  default:
                    // Check WHAT to show
                    sMsg = "General error (unspecified)";
                    if (response.err_view !== undefined) {
                      sMsg = response['err_view'];
                    } else if (response.error_list !== undefined) {
                      sMsg = response['error_list'];
                    } else {
                      // Indicate that the status is not okay
                      sMsg = "Status is not good. It is: " + response.status;
                    }
                    // Show the message at the appropriate location
                    $(elErr).html("<div class='error'>" + sMsg + "</div>");
                    // Make sure events are in place again
                    ru.basic.init_events();
                    switch (sFtype) {
                      case "cvar":
                        ru.basic.init_cvar_events();
                        break;
                      case "cond":
                        ru.basic.init_cond_events();
                        break;
                      case "feat":
                        ru.basic.init_feat_events();
                        break;
                    }
                    // Indicate we are through with waiting
                    private_methods.waitStop(elWait);
                    $(".save-warning").html("(not saved)");
                    break;
                }
              }
              private_methods.waitStop(elWait);
            }, function (progress, value) {
              // Show  progress of uploading to the user
              console.log(progress);
              $(elProg).val(value);
            }
          );
          // Hide progress after some time
          setTimeout(function () { $(elProg).addClass("hidden"); }, 1000);

          // Indicate waiting can stop
          private_methods.waitStop(elWait);
        } catch (ex) {
          private_methods.errMsg("import_data", ex);
          private_methods.waitStop(elWait);
        }
      },

      /**
       *  init_events
       *      Bind main necessary events
       *
       */
      init_events: function (sUrlShow, options) {
        var lHtml = [],
            elA = null,
            object_id = "",
            targetid = null,
            post_loads = [],
            sHtml = "";

        try {
          $(".ms.editable a").unbind("click").click(ru.basic.manu_edit);

          // Switch filters
          $(".badge.filter").unbind("click").click(ru.basic.filter_click);

          // No closing of certain dropdown elements on clicking
          /*
          $(".dropdown-toggle").on({
            "click": function (event) {
              var evtarget = $(event.target);
              if ($(evtarget).closest(".nocloseonclick").length) {
                $(this).data("closable", false);
              } else {
                $(this).data("closable", true);
              }
            }
          });*/

          // Make modal draggable
          $(".modal-header, modal-dragpoint").on("mousedown", function (mousedownEvt) {
            var $draggable = $(this),
                x = mousedownEvt.pageX - $draggable.offset().left,
                y = mousedownEvt.pageY - $draggable.offset().top;

            $("body").on("mousemove.draggable", function (mousemoveEvt) {
              $draggable.closest(".modal-dialog").offset({
                "left": mousemoveEvt.pageX - x,
                "top": mousemoveEvt.pageY - y
              });
            });
            $("body").one("mouseup", function () {
              $("body").off("mousemove.draggable");
            });
            $draggable.closest(".modal").one("bs.modal.hide", function () {
              $("body").off("mousemove.draggable");
            });
          });


          $(".nocloseonclick").each(function (idx, value) {
            var targetid = $(this);
            $(targetid).data("closable", false);
            $(targetid).on("click", function (event) {
              event.stopPropagation();
            });
          });

          // Look for options
          if (options !== undefined) {
            // Evaluate that object
            if ('isnew' in options && options['isnew']) {
              // Make sure the 'new' is triggered
              $(".edit-mode").removeClass("hidden");
              $(".view-mode").addClass("hidden");
              // This is 'new', so don't show buttons cancel and delete
              $("a[mode='cancel'], a[mode='delete']").addClass("hidden");
              // Since this is new, don't show fields that may not be shown for new
              $(".edit-notnew").addClass("hidden");
              $(".edit-new").removeClass("hidden");
            }
          }

          // See if there are any post-loads to do
          $(".post-load").each(function (idx, value) {
            var targetid = $(this);
            post_loads.push(targetid);
            // Remove the class
            $(targetid).removeClass("post-load");
          });

          // Now address all items from the list of post-load items
          post_loads.forEach(function (targetid, index) {
            var data = [],
                lst_ta = [],
                i = 0,
                targeturl = $(targetid).attr("targeturl");

            // Load this one with a GET action
            $.get(targeturl, data, function (response) {
              // Remove the class
              $(targetid).removeClass("post-load");

              // Action depends on the response
              if (response === undefined || response === null || response.status === undefined) {
                private_methods.errMsg("No status returned");
              } else {
                switch (response.status) {
                  case "ok":
                    // Show the result
                    $(targetid).html(response['html']);
                    // Call initialisation again
                    ru.basic.init_events(sUrlShow);
                    // Handle type aheads
                    if (response.typeaheads !== undefined) {
                      // Perform typeahead for these ones
                      // ru.basic.init_event_listeners(response.typeaheads);
                    }
                    break;
                  case "error":
                    // Show the error
                    if (response.msg !== undefined) {
                      $(targetid).html(response.msg);
                    } else {
                      $(targetid).html("An error has occurred (basic init_events)");
                    }
                    break;
                }
              }

            });
          });

          // Set handling of unique-field
          $("td.unique-field input").unbind("change").change(ru.basic.unique_change);

          // Allow "Search on ENTER" from typeahead fields
          $(".form-row:not(.empty-form) .searching").on("keypress",
            function (evt) {
              var key = evt.which,  // Get the KEY information
                  start = null,
                  button = null;

              // Look for ENTER
              if (key === KEYS.ENTER) {
                // Find the 'Search' button
                button = $(this).closest("form").find("a[role=button]").last();
                // Check for the inner text
                if ($(button)[0].innerText === "Search") {
                  // Found it
                  $(button).click();
                  evt.preventDefault();
                }
              }
            });

          // Make sure select2 is initialized correctly
          // NOTE: what about select2_options?
          //    $(".django-select2").djangoSelect2(select2_options);
          // $(".django-select2").djangoSelect2();
          $(".django-select2").each(function (idx, el) {
            var elTd = null,
                lst_parts = [],
                i = 0,
                options = {},
                template_fn = null,
                template_sel = null;

            // elTd = $(el).closest("td");
            elTd = $(el).closest("[select2init]");
            template_sel = $(elTd).attr("select2init");
            if (template_sel !== undefined && template_sel != "") {
              // Should be a function 
              template_fn = window[template_sel];
              if (typeof template_fn === "function") {
                //$(el).find(".django-select2").djangoSelect2(template_fn);
              } else {
                lst_parts = template_sel.split(".");
                template_fn = window;
                for (i = 0; i < lst_parts.length; i++) {
                  template_fn = template_fn[lst_parts[i]];
                }
                //$(el).find(".django-select2").djangoSelect2(template_fn);
              }
              // Create the option to be passed on
              options["templateSelection"] = template_fn;
              // Remove previous .select2
              $(el).parent().find(".select2").remove();
              // Now make it happen
              $(el).parent().find(".django-select2").djangoSelect2(options);
            }
          });

        } catch (ex) {
          private_methods.errMsg("init_events", ex);
        }
      },

      /**
       * init_typeahead
       *    Initialize the typeahead features, based on the existing bloodhound stuff
       */
      init_typeahead: function () {
        try {

          // Set handling of unique-field
          $("td.unique-field input").unbind("change").change(ru.basic.unique_change);

          // Look for <select> or <input> with [tdstyle]
          $("select[tdstyle], input[tdstyle]").each(function (idx, el) {
            var td = $(el).closest("td");

            if (! $(td)[0].hasAttribute("style")) {
              $(td).attr("style", $(el).attr("tdstyle"));
            }
          });

          // First destroy them
          $(".typeahead.keywords").typeahead('destroy');
          $(".typeahead.languages").typeahead('destroy');

          // Type-ahead: KEYWORD -- NOTE: not in a form-row, but in a normal 'row'
          $(".row .typeahead.keywords, tr .typeahead.keywords").typeahead(
            { hint: true, highlight: true, minLength: 1 },
            {
              name: 'keywords', source: loc_keyword, limit: 25, displayKey: "name",
              templates: {
                empty: '<p>Use the wildcard * to mark an inexact wording of a keyword</p>',
                suggestion: function (item) {
                  return '<div>' + item.name + '</div>';
                }
              }
            }
          ).on('typeahead:selected typeahead:autocompleted', function (e, suggestion, name) {
            $(this).closest("td").find(".keyword-key input").last().val(suggestion.id);
          });

          // Type-ahead: LANGUAGE -- NOTE: not in a form-row, but in a normal 'row'
          $(".row .typeahead.languages, tr .typeahead.languages").typeahead(
            { hint: true, highlight: true, minLength: 1 },
            {
              name: 'languages', source: loc_language, limit: 25, displayKey: "name",
              templates: {
                empty: '<p>Use the wildcard * to mark an inexact wording of a language</p>',
                suggestion: function (item) {
                  return '<div>' + item.name + '</div>';
                }
              }
            }
          ).on('typeahead:selected typeahead:autocompleted', function (e, suggestion, name) {
            $(this).closest("td").find(".language-key input").last().val(suggestion.id);
          });

          // Make sure we know which element is pressed in typeahead
          $(".form-row:not(.empty-form) .typeahead").on("keyup",
            function () {
              loc_elInput = $(this);
            });

          // Make sure the twitter typeahead spans are maximized
          $("span.twitter-typeahead").each(function () {
            var style = $(this).attr("style");
            $(this).attr("style", style + " width: 100%;");
          });

        } catch (ex) {
          private_methods.errMsg("init_typeahead", ex);
        }
      },

      /**
       * manu_edit
       *   Switch between edit modes on this <tr>
       *   And if saving is required, then call the [targeturl] to send a POST of the form data
       *
       */
      manu_edit: function (el, sType, oParams) {
        var //el = this,
            sMode = "",
            colspan = "",
            targeturl = "",
            targetid = "",
            afterurl = "",
            targethead = null,
            lHtml = [],
            data = null,
            key = "",
            i = 0,
            frm = null,
            bOkay = true,
            bReloading = false,
            manutype = "",
            err = "#little_err_msg",
            elTr = null,
            elUserDetails = "#add_to_details",
            elView = null,
            elEdit = null;

        try {
          // Possibly correct [el]
          if (el !== undefined && "currentTarget" in el) { el = el.currentTarget; }
          // Get the mode
          if (sType !== undefined && sType !== "") {
            sMode = sType;
          } else {
            sMode = $(el).attr("mode");
          }
          // Get the <tr>
          elTr = $(el).closest("td");
          // Get the manutype
          manutype = $(el).attr("manutype");
          if (manutype === undefined) { manutype = "other"; }

          // Get alternative parameters from [oParams] if this is defined
          if (oParams !== undefined) {
            if ('manutype' in oParams) { manutype = oParams['manutype']; }
          }

          // Check if we need to take the table
          if ($(elTr).hasClass("table")) {
            elTr = $(el).closest("table");
          }
          // Get the view and edit values
          elView = $(el).find(".view-mode").first();
          elEdit = $(el).find(".edit-mode").first();

          // Action depends on the mode
          switch (sMode) {
            case "skip":
              return;
              break;
            case "edit":
              // Make sure all targetid's that need opening are shown
              $(elTr).find(".view-mode:not(.hidden)").each(function () {
                var elTarget = $(this).attr("targetid");
                var targeturl = $(this).attr("targeturl");

                frm = $(el).closest("form");
                data = frm.serializeArray();
                if (elTarget !== undefined && elTarget !== "") {
                  // Do we have a targeturl?
                  if (targeturl !== undefined && targeturl !== "") {
                    // Make a post to the targeturl
                    $.post(targeturl, data, function (response) {
                      // Action depends on the response
                      if (response === undefined || response === null || response.status === undefined) {
                        private_methods.errMsg("No status returned");
                      } else {
                        switch (response.status) {
                          case "ready":
                          case "ok":
                            if (response.html !== undefined) {
                              // Show the HTML in the targetid
                              $("#" + elTarget).html(response['html']);
                            }
                            // In all cases: open the target
                            $("#" + elTarget).removeClass("hidden");
                            // And make sure typeahead works
                            ru.basic.init_typeahead();
                            break;
                        }
                      }
                    });
                  } else {
                    // Just open the target
                    $("#" + elTarget).removeClass("hidden");
                  }
                }
              });
              // Go to edit mode
              $(elTr).find(".view-mode").addClass("hidden");
              $(elTr).find(".edit-mode").removeClass("hidden");
              // Hide afterdetails
              $(elUserDetails).addClass("hidden");
              // Make sure typeahead works here
              ru.basic.init_typeahead();
              break;
            case "view":
            case "new":
              // Get any possible targeturl
              targeturl = $(el).attr("targeturl");
              targetid = $(el).attr("targetid");
              // If the targetid is specified, we need to get it from there
              if (targetid === undefined || targetid === "") {
                // No targetid specified: just open the target url
                window.location.href = targeturl;
              } else if (loc_bManuSaved) {
                loc_bManuSaved = false;
                // Refresh page
                window.location.href = window.location.href;
              } else {
                switch (manutype) {
                  case "goldlink":
                  case "goldnew":
                  case "newgoldlink":
                    targethead = $("#" + targetid);
                    break;
                  case "goldlinkclose":
                    targethead = $("#" + targetid).closest(".goldlink");
                    $(targethead).addClass("hidden");
                    $(elTr).find(".edit-mode").addClass("hidden");
                    $(elTr).find(".view-mode").removeClass("hidden");
                    return;
                  default:
                    targethead = $("#" + targetid).closest("tr.gold-head");
                    if (targethead !== undefined && targethead.length > 0) {
                      // Targetid is specified: check if we need to close
                      if (!$(targethead).hasClass("hidden")) {
                        // Close it
                        $(targethead).addClass("hidden");
                        return;
                      }
                    } else if ($("#" + targetid).attr("showing") !== undefined) {
                      if ($("#" + targetid).attr("showing") === "true") {
                        $("#" + targetid).attr("showing", "false");
                        $("#" + targetid).html("");
                        return;
                      }
                    }
                    break;
                }

                // There is a targetid specified, so make a GET request for the information and get it here
                data = [];
                // Check if there are any parameters in [oParams]
                if (oParams !== undefined) {
                  for (key in oParams) {
                    data.push({ 'name': key, 'value': oParams[key] });
                  }
                }

                $.get(targeturl, data, function (response) {
                  // Action depends on the response
                  if (response === undefined || response === null || response.status === undefined) {
                    private_methods.errMsg("No status returned");
                  } else {
                    switch (response.status) {
                      case "ready":
                      case "ok":
                      case "error":
                        if (response.html !== undefined) {
                          // Show the HTML in the targetid
                          $("#" + targetid).html(response['html']);
                          // Make sure invisible ancestors show up
                          $("#" + targetid).closest(".hidden").removeClass("hidden");
                          // Indicate that we are showing here
                          $("#" + targetid).attr("showing", "true");

                          switch (manutype) {
                            case "goldsermon":
                              // Close any other edit-mode items
                              $(targethead).closest("table").find(".edit-mode").addClass("hidden");
                              // Open this particular edit-mode item
                              $(targethead).removeClass("hidden");
                              break;
                            case "goldlink":
                              $(el).closest("table").find(".edit-mode").addClass("hidden");
                              $(el).closest("table").find(".view-mode").removeClass("hidden");
                              $(elTr).find(".edit-mode").removeClass("hidden");
                              $(elTr).find(".view-mode").addClass("hidden");
                              break;
                            case "goldnew":
                              // Use the new standard approach for *NEW* elements
                              $("#" + targetid).closest(".subform").find(".edit-mode").removeClass("hidden");
                              $("#" + targetid).closest(".subform").find(".view-mode").addClass("hidden");
                              break;
                            default:
                              break;
                          }

                          // Check on specific modes
                          if (sMode === "new") {
                            $("#" + targetid).find(".edit-mode").removeClass("hidden");
                            $("#" + targetid).find(".view-mode").addClass("hidden");
                            // This is 'new', so don't show buttons cancel and delete
                            $("#" + targetid).find("a[mode='cancel'], a[mode='delete']").addClass("hidden");
                            // Since this is new, don't show fields that may not be shown for new
                            $("#" + targetid).find(".edit-notnew").addClass("hidden");
                            $("#" + targetid).find(".edit-new").removeClass("hidden");
                          } else {
                            // Just viewing means we can also delete...
                            // What about CANCEL??
                            // $("#" + targetid).find("a[mode='delete']").addClass("hidden");
                          }

                          // If there is an error, indicate this
                          if (response.status === "error") {
                            if (response.msg !== undefined) {
                              if (typeof response['msg'] === "object") {
                                lHtml = []
                                lHtml.push("Errors:");
                                $.each(response['msg'], function (key, value) { lHtml.push(key + ": " + value); });
                                $(err).html(lHtml.join("<br />"));
                              } else {
                                $(err).html("Error: " + response['msg']);
                              }
                            } else {
                              $(err).html("<code>There is an error</code>");
                            }
                          }
                        } else {
                          // Send a message
                          $(err).html("<i>There is no <code>html</code> in the response from the server</i>");
                        }
                        break;
                      default:
                        // Something went wrong -- show the page or not?
                        $(err).html("The status returned is unknown: " + response.status);
                        break;
                    }
                  }
                  switch (manutype) {
                    case "goldlink":
                    case "goldnew":
                      break;
                    default:
                      // Return to view mode
                      $(elTr).find(".view-mode").removeClass("hidden");
                      $(elTr).find(".edit-mode").addClass("hidden");
                      // Hide waiting symbol
                      $(elTr).find(".waiting").addClass("hidden");
                      break;
                  }
                  // Perform init again
                  ru.basic.init_typeahead();
                  ru.basic.init_events();
                });

              }
              break;
            case "save":
              // Do we have an afterurl?
              afterurl = $(el).attr("afterurl");

              // Show waiting symbol
              $(elTr).find(".waiting").removeClass("hidden");

              // Make sure we know where the error message should come
              if ($(err).length === 0) { err = $(".err-msg").first(); }

              // Get any possible targeturl
              targeturl = $(el).attr("targeturl");
              targetid = $(el).attr("targetid");

              // What if no targetid is specified?
              if (targetid === undefined || targetid === "") {
                // Then we need the parent of our closest enclosing table
                targetid = $(el).closest("form").parent();
              } else {
                targetid = $("#" + targetid);
              }

              // Check
              if (targeturl === undefined) { $(err).html("Save: no <code>targeturl</code> specified"); bOkay = false }
              if (bOkay && targetid === undefined) { $(err).html("Save: no <code>targetid</code> specified"); }

              // Get the form data
              frm = $(el).closest("form");
              if (bOkay && frm === undefined) { $(err).html("<i>There is no <code>form</code> in this page</i>"); }

              // Either POST the request
              if (bOkay) {
                // Get the data into a list of k-v pairs
                // data = $(frm).serializeArray();
                // NOTE: only this will provide the correct stuff
                data = new FormData($(frm)[0]);
                // Adapt the value for the [library] based on the [id] 
                // Try to save the form data: send a POST
                //$.post(targeturl, data, function (response) {
                $.ajax({
                  url: targeturl, type: 'post', data: data, async: true,
                  contentType: false, processData: false,
                  success: function (response) {
                    // Action depends on the response
                    if (response === undefined || response === null || response.status === undefined) {
                      private_methods.errMsg("No status returned");
                    } else {
                      switch (response.status) {
                        case "error":
                          // Indicate there is an error
                          bOkay = false;
                          // Show the error in an appropriate place
                          if (response.msg !== undefined) {
                            if (typeof response['msg'] === "object") {
                              lHtml = [];
                              lHtml.push("Errors:");
                              $.each(response['msg'], function (key, value) { lHtml.push(key + ": " + value); });
                              $(err).html(lHtml.join("<br />"));
                            } else {
                              $(err).html("Error: " + response['msg']);
                            }
                          } else if (response.errors !== undefined) {
                            lHtml = [];
                            lHtml.push("<h4>Errors</h4>");
                            for (i = 0; i < response['errors'].length; i++) {
                              $.each(response['errors'][i], function (key, value) {
                                lHtml.push("<b>" + key + "</b>: </i>" + value + "</i>");
                              });
                            }
                            $(err).html(lHtml.join("<br />"));
                          } else if (response.error_list !== undefined) {
                            lHtml = [];
                            lHtml.push("Errors:");
                            $.each(response['error_list'], function (key, value) { lHtml.push(key + ": " + value); });
                            $(err).html(lHtml.join("<br />"));
                          } else {
                            $(err).html("<code>There is an error</code>");
                          }
                          break;
                        case "ready":
                        case "ok":
                          // First check for afterurl
                          if (afterurl !== undefined && afterurl !== "") {
                            // Make sure we go to the afterurl
                            window.location = afterurl;
                          }
                          if ("html" in response) {
                            // Show the HTML in the targetid
                            $(targetid).html(response['html']);
                            // Signal globally that something has been saved
                            loc_bManuSaved = true;
                            // If an 'afternewurl' is specified, go there
                            if ('afternewurl' in response && response['afternewurl'] !== "") {
                              window.location = response['afternewurl'];
                              bReloading = true;
                            } else {
                              // nothing else yet
                            }
                          } else {
                            // Send a message
                            $(err).html("<i>There is no <code>html</code> in the response from the server</i>");
                          }
                          break;
                        default:
                          // Something went wrong -- show the page or not?
                          $(err).html("The status returned is unknown: " + response.status);
                          break;
                      }
                    }
                    if (!bReloading && bOkay) {
                      // Return to view mode
                      $(elTr).find(".view-mode").removeClass("hidden");
                      $(elTr).find(".edit-mode").addClass("hidden");
                      // Hide waiting symbol
                      $(elTr).find(".waiting").addClass("hidden");
                      // If we get here, switch on afterdetails again
                      $(elUserDetails).removeClass("hidden");
                      // Perform init again
                      ru.basic.init_events();
                    }
                    }
                  }
                );
              } else {
                // Or else stop waiting - with error message above
                $(elTr).find(".waiting").addClass("hidden");
              }

              break;
            case "cancel":
              // Make sure all targetid's that need closing are hidden
              $(elTr).find(".edit-mode:not(.hidden)").each(function () {
                var elTarget = $(this).attr("targetid");
                if (elTarget !== undefined && elTarget !== "") {
                  $("#" + elTarget).addClass("hidden");
                }
              });
              // Go to view mode without saving
              $(elTr).find(".view-mode").removeClass("hidden");
              $(elTr).find(".edit-mode").addClass("hidden");
              // If we get here, switch on afterdetails again
              $(elUserDetails).removeClass("hidden");
              break;
            case "delete":
              // Do we have an afterurl?
              afterurl = $(el).attr("afterurl");

              // Check if we are under a delete-confirm
              if ($(el).closest("div[delete-confirm]").length === 0) {
                // Ask for confirmation
                // NOTE: we cannot be more specific than "item", since this can be manuscript or sermongold
                if (!confirm("Do you really want to remove this item?")) {
                  // Return from here
                  return;
                }
              }
              // Show waiting symbol
              $(elTr).find(".waiting").removeClass("hidden");

              // Get any possible targeturl
              targeturl = $(el).attr("targeturl");

              // Determine targetid from own
              targetid = $(el).closest(".gold-head");
              targethead = $(targetid).prev();

              // Check
              if (targeturl === undefined) { $(err).html("Save: no <code>targeturl</code> specified"); bOkay = false }

              // Get the form data
              frm = $(el).closest("form");
              if (bOkay && frm === undefined) { $(err).html("<i>There is no <code>form</code> in this page</i>"); }
              // Either POST the request
              if (bOkay) {
                // Get the data into a list of k-v pairs
                data = $(frm).serializeArray();
                // Add the delete mode
                data.push({ name: "action", value: "delete" });

                // Try to delete: send a POST
                $.post(targeturl, data, function (response) {
                  // Action depends on the response
                  if (response === undefined || response === null || !("status" in response)) {
                    private_methods.errMsg("No status returned");
                  } else {
                    switch (response.status) {
                      case "ready":
                      case "ok":
                        // Do we have afterdelurl afterurl?
                        // If an 'afternewurl' is specified, go there
                        if ('afterdelurl' in response && response['afterdelurl'] !== "") {
                          window.location = response['afterdelurl'];
                          return;
                        } else if (afterurl === undefined || afterurl === "") {
                          // Delete visually
                          $(targetid).remove();
                          $(targethead).remove();
                        } else {
                          // Make sure we go to the afterurl
                          window.location = afterurl;
                          return;
                        }
                        break;
                      case "error":
                        if ("html" in response) {
                          // Show the HTML in the targetid
                          $(err).html(response['html']);
                          // If there is an error, indicate this
                          if (response.status === "error") {
                            if ("msg" in response) {
                              if (typeof response['msg'] === "object") {
                                lHtml = []
                                lHtml.push("Errors:");
                                $.each(response['msg'], function (key, value) { lHtml.push(key + ": " + value); });
                                $(err).html(lHtml.join("<br />"));
                              } else {
                                $(err).html("Error: " + response['msg']);
                              }
                            } else {
                              $(err).html("<code>There is an error</code>");
                            }
                          }
                        } else {
                          // Send a message
                          $(err).html("<i>There is no <code>html</code> in the response from the server</i>");
                        }
                        break;
                      default:
                        // Something went wrong -- show the page or not?
                        $(err).html("The status returned is unknown: " + response.status);
                        break;
                    }
                  }
                  // Return to view mode
                  $(elTr).find(".view-mode").removeClass("hidden");
                  $(elTr).find(".edit-mode").addClass("hidden");
                  // Hide waiting symbol
                  $(elTr).find(".waiting").addClass("hidden");
                  // Perform init again
                  ru.basic.init_events();
                });
              } else {
                // Or else stop waiting - with error message above
                $(elTr).find(".waiting").addClass("hidden");
              }


              break;
          }

        } catch (ex) {
          private_methods.errMsg("manu_edit", ex);
        }
      },

      /**
        * post_download
        *   Trigger creating and downloading a result CSV / XLSX / JSON
        *
        */
      post_download: function (elStart, options) {
        var ajaxurl = "",
            action = "",
            contentid = null,
            response = null,
            call_onready = null,
            call_onstart = null,
            scaleFactor = 4,  // Scaling of images to make sure the result is not blurry
            frm = null,
            el = null,
            canvas = null,
            elData = null,
            sHtml = "",
            oBack = null,
            // options = {},
            dtype = "",
            bProcessing = false,
            data = "",
            sMsg = "",
            svgText = "",
            request = null,
            waitclass = null,
            method = "xhtp",  // Options: 'normal', 'erwin', 'xhtp'
            data = [];

        try {
          // Clear the errors
          private_methods.errClear();

          // obligatory parameter: ajaxurl
          ajaxurl = $(elStart).attr("ajaxurl");
          contentid = $(elStart).attr("contentid");

          if (options !== undefined) {
            if ("waitclass" in options) { waitclass = "." + options.waitclass; }
            if ("onready" in options) { call_onready = options.onready; }
            if ("onstart" in options) { call_onstart = options.onstart; }
          }

          // Gather the information
          frm = $(elStart).closest(".container-small").find("form");
          if (frm.length === 0) {
            frm = $(elStart).closest("td").find("form");
            if (frm.length === 0) {
              frm = $(elStart).closest(".body-content").find("form");
              if (frm.length === 0) {
                frm = $(elStart).closest(".container-large.body-content").find("form");
              }
            }
          }
          // Check what we have
          if (frm === null || frm.length === 0) {
            // Didn't find the form
            private_methods.errMsg("post_download: could not find form");
          } else {
            // Make sure we take only the first matching form
            frm = frm.first();
          }
          // Get the download type and put it in the <input>
          dtype = $(elStart).attr("downloadtype");
          $(frm).find("#downloadtype").val(dtype);

          switch (method) {
            case "erwin":
              data = frm.serialize();
              $.post(ajaxurl, data, function (response) {
                var iready = 1;
              });
              break;
            case "xhtp":
              request = new XMLHttpRequest();
              // Create the request
              request.open('POST', ajaxurl, true);
              request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
              request.responseType = 'blob';
              // Function for when it is loaded
              request.onload = function (e) {
                if (this.status === 200) {
                  var filename = "",
                      disposition = request.getResponseHeader('Content-Disposition');

                  // check if filename is given
                  if (disposition && disposition.indexOf('attachment') !== -1) {
                    let filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    let matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');
                  }
                  let blob = this.response;
                  if (window.navigator.msSaveOrOpenBlob) {
                    window.navigator.msSaveBlob(blob, filename);
                  }
                  else {
                    let downloadLink = window.document.createElement('a');
                    let contentTypeHeader = request.getResponseHeader("Content-Type");
                    downloadLink.href = window.URL.createObjectURL(new Blob([blob], { type: contentTypeHeader }));
                    downloadLink.download = filename;
                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);
                  }
                } else {
                  alert('Download failed');
                }
              }

              // What to do when request is finished
              request.onreadystatechange = function () {
                if (this.readyState === 4 && call_onready !== null) {
                  // Call the function on ready
                  call_onready(elStart);
                }
              }

              // Call the function on start
              if (call_onstart !== null) { call_onstart(elStart); }

              // Do we have a contentid?
              if (contentid !== undefined && contentid !== null && contentid !== "") {
                // Generic
                elData = $(frm).find("#downloaddata");
                // Process download data
                switch (dtype) {
                  case "hist-png":  // Download (histogram) as PNG
                    // Need to show waiting?
                    if (waitclass !== null) {
                      // Start waiting
                      $(frm).find(waitclass).removeClass("hidden");
                      $(frm).find(".dropdown-menu").addClass("hidden");
                    }

                    // Convert the HTML into a canvas and turn the canvas into a PNG
                    el = $(contentid).first().get(0);

                    el.scrollIntoView();
                    html2canvas(el, {
                      scale: scaleFactor, y: window.scrollY, x: window.scrollX,
                      logging: true, foreignObjectRendering: true,
                      removeContainer: true
                    })
                      .then(function (canvas) {
                        // Convert to data
                        var imageData = canvas.toDataURL("image/png");
                        if (elData.length > 0) {
                          $(elData).val(imageData);
                        }

                        // Need to stop showing waiting?
                        if (waitclass !== null) {
                          // Start waiting
                          $(frm).find(waitclass).addClass("hidden");
                        }

                        // Now submit the form with the proper data
                        data = $(frm).serialize();
                        request.send(data);

                        // Call the function on ready
                        if (call_onready !== null) { call_onready(elStart); }

                      });
                    bProcessing = true;
                    break;
                  case "hist-svg":
                    sHtml = private_methods.prepend_styles(contentid, "svg");
                    // Set it
                    if (elData.length > 0) {
                      $(elData).val(sHtml);
                    }
                    // Now send it with the proper data
                    data = $(frm).serialize();
                    request.send(data);

                    // Call the function on ready
                    if (call_onready !== null) { call_onready(elStart); }
                    bProcessing = true;
                    break;
                }
              } 
              // If it hasn't yet been processed
              if (!bProcessing) {
                // Process download data
                switch (dtype) {
                  case "json":
                  case "xlsx":
                  case "csv":
                    // Need to show waiting?
                    if (waitclass !== null) {
                      // Start waiting
                      $(frm).find(waitclass).removeClass("hidden");
                      $(frm).find(".dropdown-menu").addClass("hidden");
                    }
                    // Now send it with proper data
                    data = $(frm).serialize();
                    request.send(data);

                    // Note: the 'onreadystate' function picks up the onready callback
                    // DO NOT put a callback here!
                    break;
                  default:
                    // TODO: add error message here
                    return;
                }
              }

              break;
            default:
              // Set the 'action; attribute in the form
              action = frm.attr("action");
              frm.attr("action", ajaxurl);
              // Make sure we do a POST
              frm.attr("method", "POST");

              // Do we have a contentid?
              if (contentid !== undefined && contentid !== null && contentid !== "") {
                // Generic
                elData = $(frm).find("#downloaddata");
                // Process download data
                switch (dtype) {
                  case "hist-png":  // Download (histogram) as PNG
                    // Need to show waiting?
                    if (waitclass !== null) {
                      // Start waiting
                      $(frm).find(waitclass).removeClass("hidden");
                      $(frm).find(".dropdown-menu").addClass("hidden");
                    }

                    // Convert the HTML into a canvas and turn the canvas into a PNG
                    el = $(contentid).first().get(0);

                    el.scrollIntoView();
                    html2canvas(el, {
                      scale: scaleFactor, y: window.scrollY, x: window.scrollX,
                      logging: true, foreignObjectRendering: true,
                      removeContainer: true
                    })
                      .then(function (canvas) {
                        // Convert to data
                        var imageData = canvas.toDataURL("image/png");
                        if (elData.length > 0) {
                          $(elData).val(imageData);
                        }

                        // Need to stop showing waiting?
                        if (waitclass !== null) {
                          // Start waiting
                          $(frm).find(waitclass).addClass("hidden");
                        }

                        // Now submit the form
                        oBack = frm.submit();

                      });
                    break;
                  case "hist-svg":
                    sHtml = private_methods.prepend_styles(contentid, "svg");
                    // Set it
                    if (elData.length > 0) {
                      $(elData).val(sHtml);
                    }
                    // Now submit the form
                    oBack = frm.submit();
                    break;
                  case "json":
                  case "xlsx":
                    // Need to show waiting?
                    if (waitclass !== null) {
                      // Start waiting
                      $(frm).find(waitclass).removeClass("hidden");
                      $(frm).find(".dropdown-menu").addClass("hidden");
                    }
                    // Now submit the form
                    oBack = frm.submit();
                    break;
                  default:
                    // TODO: add error message here
                    return;
                }
              } else {
                // Need to show waiting?
                if (waitclass !== null) {
                  // Start waiting
                  $(frm).find(waitclass).removeClass("hidden");
                  $(frm).find(".dropdown-menu").addClass("hidden");
                }
                // Do a plain submit of the form
                oBack = frm.submit();

              }
              break;
          }

          // Check on what has been returned
          if (oBack !== null) {

          }
        } catch (ex) {
          private_methods.errMsg("post_download", ex);
        }
      },

      /**
       * search_reset
       *    Clear the information in the form's fields and then do a submit
       *
       */
      search_reset: function (elStart) {
        var frm = null;

        try {
          // Get to the form
          frm = $(elStart).closest('form');
          // Clear the information in the form's INPUT fields
          $(frm).find("input:not([readonly]).searching").val("");
          // Show we are waiting
          $("#waitingsign").removeClass("hidden");
          // Now submit the form
          frm.submit();
        } catch (ex) {
          private_methods.errMsg("search_reset", ex);
        }
      },

      /**
       * search_clear
       *    No real searching, just reset the criteria
       *
       */
      search_clear: function (elStart) {
        var frm = null,
            idx = 0,
            lFormRow = [];

        try {
          // Clear filters
          $(".badge.filter").each(function (idx, elThis) {
            var target;

            target = $(elThis).attr("targetid");
            if (target !== undefined && target !== null && target !== "") {
              target = $("#" + target);
              // Action depends on checking or not
              if ($(elThis).hasClass("on")) {
                // it is on, switch it off
                $(elThis).removeClass("on");
                $(elThis).removeClass("jumbo-3");
                $(elThis).addClass("jumbo-1");
                // Must hide it and reset target
                $(target).addClass("hidden");
                $(target).find("input").each(function (idx, elThis) {
                  $(elThis).val("");
                });
                // Also reset all select 2 items
                $(target).find("select").each(function (idx, elThis) {
                  $(elThis).val("").trigger("change");
                });
              }
            }
          });

        } catch (ex) {
          private_methods.errMsg("search_clear", ex);
        }
      },

      /**
       * search_start
       *    Gather the information in the form's fields and then do a submit
       *
       */
      search_start: function (elStart, method, iPage, sOrder) {
        var frm = null,
            url = "",
            targetid = null,
            targeturl = "",
            data = null;

        try {
          // Get to the form
          frm = $(elStart).closest('form');
          // Get the data from the form
          data = frm.serializeArray();

          // Determine the method
          if (method === undefined) { method = "submit"; }

          // Get the URL from the form
          url = $(frm).attr("action");

          // Action depends on the method
          switch (method) {
            case "submit":
              // Show we are waiting
              $("#waitingsign").removeClass("hidden");
              // Store the current URL
              loc_urlStore = url;
              // If there is a page number, we need to process it
              if (iPage !== undefined) {
                $(elStart).find("input[name=page]").each(function (el) {
                  $(this).val(iPage);
                });
              }
              // If there is a sort order, we need to process it
              if (sOrder !== undefined) {
                $(elStart).find("input[name=o]").each(function (el) {
                  $(this).val(sOrder);
                });
              }
              // Now submit the form
              frm.submit();
              break;
            case "post":
              // Determine the targetid
              targetid = $(elStart).attr("targetid");
              if (targetid == "subform") {
                targetid = $(elStart).closest(".subform");
              } else {
                targetid = $("#" + targetid);
              }
              // Get the targeturl
              targeturl = $(elStart).attr("targeturl");

              // Get the page we need to go to
              if (iPage === undefined) { iPage = 1; }
              data.push({ 'name': 'page', 'value': iPage });
              if (sOrder !== undefined) {
                data.push({ 'name': 'o', 'value': sOrder });
              }

              // Issue a post
              $.post(targeturl, data, function (response) {
                // Action depends on the response
                if (response === undefined || response === null || !("status" in response)) {
                  private_methods.errMsg("No status returned");
                } else {
                  switch (response.status) {
                    case "ready":
                    case "ok":
                      // Show the HTML target
                      $(targetid).html(response['html']);
                      // Possibly do some initialisations again??

                      // Make sure events are re-established
                      // ru.passim.seeker.init_events();
                      ru.passim.init_typeahead();
                      break;
                    case "error":
                      // Show the error
                      if ('msg' in response) {
                        $(targetid).html(response.msg);
                      } else {
                        $(targetid).html("An error has occurred (basic search_start)");
                      }
                      break;
                  }
                }
              });


              break;
          }

        } catch (ex) {
          private_methods.errMsg("search_start", ex);
        }
      },

      /**
       * search_ordered_start
       *    Perform a simple 'submit' call to search_start
       *
       */
      search_ordered_start: function (order) {
        var elStart = null;

        try {
          // And then go to the first element within the form that is of any use
          elStart = $(".search_ordered_start").first();
          ru.basic.search_start(elStart, 'submit', 1, order)
        } catch (ex) {
          private_methods.errMsg("search_ordered_start", ex);
        }
      },

      /**
       * search_paged_start
       *    Perform a simple 'submit' call to search_start
       *
       */
      search_paged_start: function (iPage) {
        var elStart = null;

        try {
          // And then go to the first element within the form that is of any use
          elStart = $(".search_paged_start").first();
          ru.basic.search_start(elStart, 'submit', iPage)
        } catch (ex) {
          private_methods.errMsg("search_paged_start", ex);
        }
      },

      /**
       * tabular_addrow
       *   Add one row into a tabular inline
       *
       */
      tabular_addrow: function (elStart, options) {
        // NOTE: see the definition of lAddTableRow above
        var oTdef = {},
            rowNew = null,
            elTable = null,
            select2_options = {},
            iNum = 0,     // Number of <tr class=form-row> (excluding the empty form)
            sId = "",
            bSelect2 = false,
            i;

        try {
          // Find out just where we are
          if (elStart === undefined || elStart === null || $(elStart).closest("div").length === 0)
            elStart = $(this);
          sId = $(elStart).closest("div[id]").attr("id");
          // Process options
          if (options !== undefined) {
            for (var prop in options) {
              switch (prop) {
                case "select2": bSelect2 = options[prop]; break;
              }
            }
          }
          // Get the definition
          oTdef = options;
          if (sId === oTdef.table || sId.indexOf(oTdef.table) >= 0) {
            // Go to the <tbody> and find the last form-row
            elTable = $(elStart).closest("tbody").children("tr.form-row.empty-form")

            if ("select2_options" in oTdef) {
              select2_options = oTdef.select2_options;
            }

            // Perform the cloneMore function to this <tr>
            rowNew = ru.basic.cloneMore(elTable, oTdef.prefix, oTdef.counter);
            // Call the event initialisation again
            if (oTdef.events !== null) {
              oTdef.events();
            }
            // Possible Select2 follow-up
            if (bSelect2) {
              // Remove previous .select2
              $(rowNew).find(".select2").remove();
              // Execute djangoSelect2()
              $(rowNew).find(".django-select2").djangoSelect2(select2_options);
            }
            // Any follow-up activity
            if ('follow' in oTdef && oTdef['follow'] !== null) {
              oTdef.follow(rowNew);
            }
          }
        } catch (ex) {
          private_methods.errMsg("tabular_addrow", ex);
        }
      },

      /**
       * tabular_deleterow
       *   Delete one row from a tabular inline
       *
       */
      tabular_deleterow: function (elStart) {
        var sId = "",
            elDiv = null,
            elRow = null,
            elPrev = null,
            elDel = null,   // The delete inbox
            sPrefix = "",
            elForms = "",
            counter = $(elStart).attr("counter"),
            deleteurl = "",
            data = [],
            frm = null,
            bCounter = false,
            bHideOnDelete = false,
            iForms = 0,
            prefix = "simplerel";

        try {
          // Get the prefix, if possible
          sPrefix = $(elStart).attr("extra");
          bCounter = (typeof counter !== typeof undefined && counter !== false && counter !== "");
          elForms = "#id_" + sPrefix + "-TOTAL_FORMS"
          // Find out just where we are
          elDiv = $(elStart).closest("div[id]")
          sId = $(elDiv).attr("id");
          // Find out how many forms there are right now
          iForms = $(elForms).val();
          frm = $(elStart).closest("form");

          // Get the deleteurl (if existing)
          deleteurl = $(elStart).attr("targeturl");
          // Only delete the current row
          elRow = $(elStart).closest("tr");
          // Do we need to hide or delete?
          if ($(elRow).hasClass("hide-on-delete")) {
            bHideOnDelete = true;
            $(elRow).addClass("hidden");
          } else {
            $(elRow).remove();
          }

          // Further action depends on whether the row just needs to be hidden
          if (bHideOnDelete) {
            // Row has been hidden: now find and set the DELETE checkbox
            elDel = $(elRow).find("input:checkbox[name$='DELETE']");
            if (elDel !== null) {
              $(elDel).prop("checked", true);
            }
          } else {
            // Decrease the amount of forms
            iForms -= 1;
            $(elForms).val(iForms);

            // Re-do the numbering of the forms that are shown
            $(elDiv).find(".form-row").not(".empty-form").each(function (idx, elThisRow) {
              var iCounter = 0, sRowId = "", arRowId = [];

              iCounter = idx + 1;
              // Adapt the ID attribute -- if it EXISTS
              sRowId = $(elThisRow).attr("id");
              if (sRowId !== undefined) {
                arRowId = sRowId.split("-");
                arRowId[1] = idx;
                sRowId = arRowId.join("-");
                $(elThisRow).attr("id", sRowId);
              }

              if (bCounter) {
                // Adjust the number in the FIRST <td>
                $(elThisRow).find("td").first().html(iCounter.toString());
              }

              // Adjust the numbering of the INPUT and SELECT in this row
              $(elThisRow).find("input, select").each(function (j, elInput) {
                // Adapt the name of this input
                var sName = $(elInput).attr("name");
                if (sName !== undefined) {
                  var arName = sName.split("-");
                  arName[1] = idx;
                  sName = arName.join("-");
                  $(elInput).attr("name", sName);
                  $(elInput).attr("id", "id_" + sName);
                }
              });
            });
          }

        } catch (ex) {
          private_methods.errMsg("tabular_deleterow", ex);
        }
      },

      /**
       * toggle_click
       *   Action when user clicks an element that requires toggling a target
       *
       */
      toggle_click: function (elThis, class_to_close) {
        var elGroup = null,
            elTarget = null,
            sStatus = "";

        try {
          // Get the target to be opened
          elTarget = $(elThis).attr("targetid");
          // Sanity check
          if (elTarget !== null) {
            // Show it if needed
            if ($("#" + elTarget).hasClass("hidden")) {
              $("#" + elTarget).removeClass("hidden");
            } else {
              $("#" + elTarget).addClass("hidden");
              // Check if there is an additional class to close
              if (class_to_close !== undefined && class_to_close !== "") {
                $("." + class_to_close).addClass("hidden");
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("toggle_click", ex);
        }
      },

      /**
       * unique_change
       *    Make sure only one input box is editable
       *
       */
      unique_change: function () {
        var el = $(this),
            elTr = null;

        try {
          elTr = $(el).closest("tr");
          $(elTr).find("td.unique-field").find("input").each(function (idx, elInput) {
            if ($(el).attr("id") !== $(elInput).attr("id")) {
              $(elInput).prop("disabled", true);
            }
          });

        } catch (ex) {
          private_methods.errMsg("unique_change", ex);
        }
      }


      // LAST POINT
    }
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

