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
        var sHtml = "Error in [" + sMsg + "]<br>" + ex.message;
        $("#" + loc_divErr).html(sHtml);
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
        var sTargetId = "research_part_",
            sTargetType = "",
            elListItem = null,
            elList = null;

        try {
          // Hide all research parts
          $(".research-part").addClass("hidden");
          $(".research-part").removeClass("active");
          // Get the correct target id
          sTargetId = "#"+ sTargetId + sPart;
          $(sTargetId).removeClass("hidden");
          // If this is not [Project Type] then get the project type
          if (sPart !== '1') {
            sTargetType = $("#id_targetType").val();
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
       * sent_click
       *   Show waiting symbol when sentence is clicked
       *
       */
      sent_click: function () {
        $("#sentence-fetch").removeClass("hidden");
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
            var name = $(this).attr('name').replace('-' + (total - 1) + '-', '-' + total + '-');
            // Produce a new id for this element
            var id = 'id_' + name;
            // Adapt this element's name and id, unchecking it
            $(this).attr({ 'name': name, 'id': id }).val('').removeAttr('checked');
          });

          // Find each <label> under newElement
          newElement.find('label').each(function () {
            // Adapt the 'for' attribute
            var newFor = $(this).attr('for').replace('-' + (total - 1) + '-', '-' + total + '-');
            $(this).attr('for', newFor);
          });

          // Adapt the total number of forms in this formset
          total++;
          $('#id_' + type + '-TOTAL_FORMS').val(total);

          // Append the new element after the selector's last child
          $(selector).after(newElement);

          // Should we re-number?
          if (number !== undefined && number) {
            // Walk all <tr> elements of the table
            var iRow = 1;
            $(selector).parent().find("tr").not(".add-row").each(function () {
              var elFirstCell = $(this).find("td:first");
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
      }

    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

