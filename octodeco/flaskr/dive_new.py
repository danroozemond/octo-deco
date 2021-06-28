import sys;

from . import dive;
from . import db_dive;
from .dive import bp;
from flask import (
    flash, redirect, url_for, request, abort, session, render_template
)

from octodeco.deco import CreateDive, Gas;


#
# New (show the page, new from spec, new demo, new from CSV)
#
@bp.route('/new', methods = [ 'GET' ])
def new_show():
    return render_template('dive/new.html');


@bp.route('/new', methods = [ 'POST' ])
def new_do():
    dtgs = [ ( request.form.get('depth[%i]' % i, None),
               request.form.get('time[%i]' % i, None),
               request.form.get('gas[%i]' % i, None) )
             for i in range(11) ];
    extragas = request.form.get('deco_gas', '');
    result = CreateDive.create_dive_by_depth_time_gas( dtgs, extragas );
    if result is None:
        # Input sanitation takes place properly in JavaScript. So if something did not work
        # out here, we're not too worried about being nice about it.
        abort(405);
    # Store, return result.
    db_dive.store_dive(result);
    return redirect(url_for('dive.show', dive_id=result.dive_id));


@bp.route('/new/demo', methods = [ 'POST' ])
def new_demo():
    dp = CreateDive.create_demo_dive();
    db_dive.store_dive(dp);
    dive_id = dp.dive_id;
    flash('Generated demo dive [%i]' % dive_id);
    return redirect(url_for('dive.show', dive_id = dive_id))


def new_csv( create_csv_func ):
    # Get the object
    if 'ipt_csv' not in request.files:
        flash('No file provided');
        return redirect(url_for('dive.new_show'));
    file = request.files['ipt_csv'];
    # Read line by line
    lines = [];
    sizeseen = 0;
    for line in file:
        lines.append(line.decode('utf-8'));
        sizeseen += sys.getsizeof(line);
        if sizeseen > 5e9:
            flash('File too big');
            return redirect(url_for('dive.new_show'));
    # Create the diveprofile object
    try:
        dp = create_csv_func( lines );
    except CreateDive.ParseError as err:
        flash( 'Error parsing CSV: %s' % err.args );
        return redirect(url_for('dive.new_show'));
    # Store the dive
    db_dive.store_dive(dp);
    dive_id = dp.dive_id;
    flash('Import successful - %s' % dp.description());
    # Done.
    return redirect(url_for('dive.show', dive_id = dive_id))


@bp.route('/new/sw_csv', methods = [ 'POST' ])
def new_shearwater_csv():
    return new_csv( CreateDive.create_from_shearwater_csv );


@bp.route('/new/od_csv', methods = [ 'POST' ])
def new_octodeco_csv():
    return new_csv( CreateDive.create_from_octodeco_csv );


@bp.route('/new/duplicate/<int:dive_id>', methods = ['GET','POST'])
def new_duplicate(dive_id):
    dp = dive.get_cached_dive(dive_id).profile_base();
    cp = dp.full_copy();
    cp.is_ephemeral = False;
    cp.is_public = False;
    # Store the dive
    db_dive.store_dive(cp);
    new_dive_id = cp.dive_id;
    flash('Duplicated {}: {}'.format(dive_id, cp.description()));
    # Done.
    return redirect(url_for('dive.show', dive_id = new_dive_id));


#
# Create ephemeral/temp dives as variant of existing ones
#
@bp.route('/new/lost/<int:dive_id>', methods = ['GET'])
def new_ephm_lost_gas(dive_id):
    req_args = dive.get_gf_args_from_request();
    lostgasstr = str(request.args.get('lostgas', ''));
    lost_gases = Gas.many_from_string(lostgasstr);
    if len(lost_gases) == 0:
        flash('Incorrect lost gas parameter');
        return redirect(url_for('dive.show', dive_id = dive_id));
    dp = dive.get_cached_dive(dive_id).profile_args(req_args);
    cp = dp.copy_profile_lost_gases(lost_gases);
    cp.is_ephemeral = True;
    cp.is_public = False;
    cp.parent_dive_id = dive_id;
    # Store the dive
    db_dive.store_dive(cp);
    dive_id = cp.dive_id;
    flash('Created scenario: %s' % cp.description());
    # Done.
    return redirect(url_for('dive.show', dive_id = dive_id))
