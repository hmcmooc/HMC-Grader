//Emulates the flash command but using javascript to create the divs

function flash(msg, type) {
  var flashBox = $("<div></div>")
  flashBox.addClass('alert');
  if (type == "warning") {
    flashBox.addClass('alert-warning');
  } else if (type == "error") {
    flashBox.addClass('alert-danger');
  } else if (type == "success") {
    flashBox.addClass('alert-success');
  } else {
    flashBox.addClass('alert-info');
  }
  flashBox.attr('role', 'alert');
  flashBox.append('<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>');
  flashBox.append(msg);
  $("#flashBox").append(flashBox)
}
