/**
 * Copyright (c) 2018 Radboud University Nijmegen.
 * All rights reserved.
 *
 * @author Erwin R. Komen
 */

/*globals jQuery, crpstudio, Crpstudio, alert: false, */
var crpstudio = (function ($, crpstudio) {
  "use strict";
  crpstudio.htable = (function ($, config) {
    // Local variables within crpstudio.htable
    var bDebug = false,         // Debugging set or not
        level = 0,              // Recursion level of vertical draw tree
        loc_oNode = {},         // Local version of current node tree
        loc_errDiv = null,      // Where to show errors
        loc_iCurrentNode = -1,  // ID of the currently selected node
        loc_bKeep = false,      // Stay on fixed position
        loc_ht1 = "func-view",
        loc_ht2 = "func-name",
        loc_ht3 = "func-link",
        loc_ht4 = "func-inline",
        loc_ht5 = "func-plus",
        loc_ht6 = "arg-text",
        loc_ht7 = "arg-line",
        loc_ht8 = "arg-summary",
        root = null;            // Root of the tree (DOM position)

    // Methods that are local to [crpstudio.dbase]
    var private_methods = {
      /**
       * adapt_htable
       *     Recursively convert a htable to one that contains summaries
       * @param {object} oHtable
       * @returns {object}
       */
      adapt_htable: function (oHtable) {
        var summary = "", // Summary
            oBack = {},
            i,
            arChild = [];

        try {
          // Validate
          if (oHtable === undefined || oHtable === null) {
            return null;
          }
          // Get text at this level
          if ('txt' in oHtable) {
            if ('type' in oHtable && oHtable['type'] !== "Star" && oHtable['type'] !== "Zero") {
              if (summary !== "") summary += " ";
              summary += oHtable['txt'];
            }
          }
          // Walk all the child tables
          if ('child' in oHtable) {
            arChild = oHtable['child'];
            for (i = 0; i < arChild.length; i++) {
              // First go down
              oBack = private_methods.adapt_htable(arChild[i]);
              // Add the summary
              if ('summary' in oBack) {
                if (summary !== "") summary += " ";
                summary += oBack['summary'];
              }
            }
          }
          // Now set the summary link
          oHtable['summary'] = summary;
          // Return the adapted table
          return oHtable
        } catch (ex) {
          // Show the error at the indicated place
          $(loc_errDiv).html("adapt_htable error: " + ex.message);
          return null;
        }
      },


      /**
       * render_htable
       *     Recursively convert a htable to an HTML string
       * @param {object} oHtable  - The table to be converted
       * @param {string} sLevel   - Either 'top' or 'descendant'
       * @returns {string}
       */
      render_htable: function(oHtable, sLevel) {
        var lHtml = [],
            oConstituent = {},
            oChild = {},
            sStretch = "",
            sText = "",
            sSign = "",
            arChild = [],
            arGchild = [],
            j,
            i;

        try {
          // This is an end-node
          if (sLevel === "descendant") {
            sStretch = "style=\"width: 100%;\"";
          }

          // Start table
          lHtml.push("<table class=\"" + loc_ht1 + "\">");

          // If this is top-level, then add a heading
          if (sLevel === "top") {
            lHtml.push("<thead><tr><th colspan=\"3\">");
            // First span
            lHtml.push("<span class=\"" + loc_ht2 + "\">");
            lHtml.push("<a class=\"btn btn-xs btn-default "+loc_ht5+"\" " +
              "role=\"button\" " +
              "title=\"open\" " +
              "onclick=\"crpstudio.htable.htablehead_click(this, '" + loc_ht4 + "');\">");
            lHtml.push("+</a>");
            lHtml.push(oHtable['pos']);
            lHtml.push("</span>&nbsp;");
            // Second span
            lHtml.push("<span class=\"" + loc_ht3 + " pull-right\">");
            lHtml.push("<a class=\"btn btn-xs btn-default \" " +
              "role=\"button\" " +
              "title=\"copy to clipboard\" " +
              "onclick=\"crpstudio.htable.copy_click(this);\">");
            lHtml.push("<span class=\"glyphicon glyphicon-open\" aria-hidden=\"true\"></span>");
            lHtml.push("</a>");
            lHtml.push("</span>");
            // Finish the thead
            lHtml.push("</th></tr></thead>");
          }

          // Start the table body
          lHtml.push("<tbody>");

          // Walk all 'child' elements -- if there are any
          if ('child' in oHtable) {
            arChild = oHtable['child'];
            for (i = 0; i < arChild.length; i++) {
              oConstituent = arChild[i];
              // First check if it has more children
              if ('child' in oConstituent) {
                // Treat all grand-children
                arGchild = oConstituent['child'];
                for (j = 0; j < arGchild.length; j++) {
                  oChild = arGchild[j];
                  // Determine the sign
                  if ('child' in oChild) {sSign = "+";} else {sSign = "";}
                  // Create the visible row
                  lHtml.push("<tr>");
                  //   [a] the plus sign
                  lHtml.push("<td class=\"arg-plus\" style=\"min-width: 20px;\" " +
                    "onclick=\"crpstudio.htable.plus_click(this, '" + loc_ht4 + "');\">"+sSign+"</td>");
                  //   [b] the middle part: POS + summary
                  lHtml.push("<td class=\"" + loc_ht6 + "\" " + sStretch + ">");
                  lHtml.push("<span class=\"" + loc_ht7 + "\"><code>" + oChild['pos'] + "</code></span>");
                  lHtml.push("<span class=\"" + loc_ht8 + "\">" + oChild['summary'] + "</span>");
                  lHtml.push("</td>");
                  //   [c] the right part: any text
                  lHtml.push(" <td align=\"right\">");
                  if ('txt' in oChild) {sText = oChild['txt'];} else {sText = "";}
                  lHtml.push("  <span>" + sText + "</span>");
                  lHtml.push(" </td>");
                  // Finish the visible row
                  lHtml.push("</tr>");

                  // Create the row that is hidden by default
                  // -- But only if there are grandchildren
                  if ('child' in oChild) {
                    lHtml.push("<tr class=\"" + loc_ht4 + " hidden\">");
                    lHtml.push(" <td style=\"width: 10px;\"></td>");
                    lHtml.push(" <td>");
                    lHtml.push(private_methods.render_htable(oChild, "descendant"));
                    lHtml.push(" </td>");
                    lHtml.push("</tr>");
                  }
                }

              } else {
                // This is an end-node
                lHtml.push("<tr>");
                lHtml.push(" <td colspan=\"2\" " + sStretch + ">");
                lHtml.push("  <span><code>" + oConstituent['pos'] + "</code></span>");
                lHtml.push("  &nbsp;</td>");
                lHtml.push(" <td align=\"right\">");
                if ('txt' in oConstituent) {sText = oConstituent['txt'];} else {sText = "";}
                lHtml.push("  <span>" + oConstituent['txt'] + "</span>");
                lHtml.push(" </td>");
                lHtml.push("</tr>");
              }
            }
          }

          // Finish the table body
          lHtml.push("</tbody>");

          // Finish the table
          lHtml.push("</table>");

          // Combine into a string and return
          return lHtml.join("\n");
        } catch (ex) {
          // Show the error at the indicated place
          $(loc_errDiv).html("render_htable error: " + ex.message);
          return "";
        }
      },

      /**
       * showError
       *     Show the error at the indicated place
       */
      showError: function (sFunction, ex) {
        var sOld = "",
            sMsg = "Error in " + sFunction + ": " + ex.message;

        if (loc_errDiv !== undefined && loc_errDiv !== null) {
          sOld = $(loc_errDiv).html();
          $(loc_errDiv).html(sOld + "<p><code>"+sMsg+"</code></p>");
        }
      },
      setErrLoc: function(sLoc) {
        loc_errDiv = sLoc;
        if (sLoc.indexOf("#")!==0) {
          loc_errDiv = "#" + loc_errDiv;
        }
        // Clear the errors
        $(loc_errDiv).html();
      },
      setNodeTree: function (oThis) {
        loc_oNode = oThis;
      }
    };

    // Methods that are exported by [crpstudio.htable] for outside functions
    return {
      ht_sign_plus : function(idx) {
        var sSign = $(this).html().trim();
        if (sSign === "-") {
          $(this).html("+");
        }
      },
      ht_sign_minus: function (idx) {
        var sSign = $(this).html().trim();
        if (sSign === "+") {
          $(this).html("-");
        } 
      },
      /**
       * htablehead_click
       *   Assuming we are on an element of class [func-plus]
       *     - close or open everything with style [sClass] below us
       *     - this depends on the 'sign' we have: + or -
       *   Also: adapt the +/- sign(s)
       */
      htablehead_click: function (el, sClass) {
        var trNext = null,
            elTbody = null, // My own <tbody>
            sStatus = "";   // My own status

        try {
          // Validate
          if (el === undefined) { return; }
          // Get my status
          sStatus = $(el).text().trim();   // This can be + or - or a SPACE
          // Get my own <tbody>
          elTbody = $(el).closest("table").children("tbody").first();
          // Check status
          if (sStatus === "-") {
            // We are open and need to close all below
            $(el).html("+");
            $(el).attr("title", "open");
            // Close all [arg-plus] below us
            $(elTbody).find(".arg-plus").each(crpstudio.htable.ht_sign_plus);
            $(elTbody).find(".func-plus").each(crpstudio.htable.ht_sign_plus);
            $(elTbody).find(".func-plus").attr("title", "open");
            $(elTbody).find(".func-inline").addClass("hidden");
          } else if (sStatus === "+") {
            // We are + (=closed) and need to open (become -)
            $(el).html("-");
            $(el).attr("title", "close");
            // Open all [arg-plus] below us
            $(elTbody).find(".arg-plus").each(crpstudio.htable.ht_sign_minus);
            $(elTbody).find(".func-plus").each(crpstudio.htable.ht_sign_minus);
            $(elTbody).find(".func-plus").attr("title", "close");
            $(elTbody).find(".func-inline").removeClass("hidden");
          }

        } catch (ex) {
          private_methods.errMsg("htablehead_click", ex);
        }
      },

      /**
       * copy_click
       *     Copy HTML of table to clipboard
       * @param {div} elThis  - Division
       * @returns {void}
       */
      copy_click: function (elThis) {
        try {

        } catch (ex) {
          private_methods.errMsg("copy_click", ex);
        }
      },

      /**
       * plus_click
       *   Show or hide the following <tr> element
       *   Also: adapt the +/- sign(s)
       */
      plus_click: function (el, sClass, bShow) {
        var trNext = null;

        try {
          // Validate
          if (el === undefined) { return; }
          if ($(el).html().trim() === "") { return;}
          // Get the following <tr>
          trNext = $(el).closest("tr").next().first();
          if (trNext !== null) {
            // Check its current status
            if ($(trNext).hasClass("hidden") || (bShow !== undefined && bShow)) {
              // Show it
              $(trNext).removeClass("hidden");
              // Change the '+' into a '-'
              if ($(el).html().trim() === "+") { $(el).html("-"); }
            } else {
              // Hide it
              $(trNext).addClass("hidden");
              // Change the '-' into a '+'
              if ($(el).html().trim() === "-") { $(el).html("+"); }
              // Hide all underlying ones with class [sClass]
              if (sClass !== undefined && sClass !== "") {
                $(trNext).find("." + sClass).addClass("hidden");
                $(trNext).find(".arg-plus").each(crpstudio.htable.ht_sign_plus);
              }
            }
          }

        } catch (ex) {
          private_methods.errMsg("plus_click", ex);
        }
      },
      /**
       * treeToHtable
       *    Convert a JSON representation of a syntax tree to SVG
       * 
       * @param {element} htDiv   - DOM where tree must come
       * @param {object} oTree    - The tree as an object
       * @param {element} errDiv  - DOM where error may appear
       * @returns {boolean}
       */
      treeToHtable: function (htDiv, oTree, errDiv) {
        var sHtml = "",
            i;

        try {
          // Validate
          if (htDiv === undefined) return false;
          if (errDiv === undefined || errDiv === null) errDiv = htDiv;
          // Set the local error div
          private_methods.setErrLoc(errDiv);

          // Adapt the nodetree to contain 'summary' elements
          oTree = private_methods.adapt_htable(oTree);

          // Be sure to keep the tree locally
          private_methods.setNodeTree(oTree);

          // Create the html for this tree
          sHtml = private_methods.render_htable(oTree, "top");

          // Show the html in place
          $(htDiv).html(sHtml);

          // Attach an event handler to all the toggles
          //$(htDiv).find(".lithium-node").click(function () { crpstudio.htable.node_fix_svg(this) });

          // Return positively
          return true;
        } catch (ex) {
          // Show the error at the indicated place
          $(errDiv).html("treeToHtable error: " + ex.message);
          return null;
        }
      }

    }

  }($, crpstudio.config));

  return crpstudio;

}(jQuery, window.crpstudio || {}));
