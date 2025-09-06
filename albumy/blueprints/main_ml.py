# Modifications for albumy/blueprints/main.py
# Add these to your existing main.py file

"""
OPTION B IMPLEMENTATION
Add these modifications to the main blueprint
"""

# Add to imports at top of file:
from albumy.semantic_ml import integrate_with_upload, semantic_search, find_similar_photos
import json

# ===== MODIFY UPLOAD ROUTE =====
# Find the existing upload route and update it:

@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@confirm_required
@permission_required('UPLOAD')
def upload():
    if request.method == 'POST' and 'image' in request.files:
        f = request.files.get('image')
        filename = rename_image(f.filename)
        
        # Save the image
        filepath = os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename)
        f.save(filepath)
        
        # Create photo record
        photo = Photo(
            filename=filename,
            filename_s=resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['small']),
            filename_m=resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['medium']),
            author=current_user._get_current_object(),
            description=request.form.get('description', '')
        )
        
        db.session.add(photo)
        db.session.commit()
        
        # Generate and store embedding (OPTION B FEATURE)
        embedding = integrate_with_upload(photo.id, filepath)
        photo.embedding_vector = json.dumps(embedding[:50])  # Store first 50 dims as sample
        db.session.commit()
        
        flash('Photo uploaded successfully!', 'success')
        return redirect(url_for('.show_photo', photo_id=photo.id))
    
    return render_template('main/upload.html')

# ===== ADD SEMANTIC SEARCH ROUTE =====

@main_bp.route('/search/semantic')
def search_semantic():
    """Option B: Semantic search endpoint."""
    q = request.args.get('q', '').strip()
    if not q:
        flash('Please enter a search query.', 'warning')
        return redirect(url_for('.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ALBUMY_SEARCH_RESULT_PER_PAGE', 20)
    
    # Perform semantic search
    photo_ids = semantic_search(q, limit=per_page * 2)
    
    # Get photos from database
    photos = []
    for photo_id in photo_ids[:per_page]:
        photo = Photo.query.get(photo_id)
        if photo:
            photos.append(photo)
    
    # Create pagination object for template compatibility
    from flask_sqlalchemy import Pagination
    pagination = Pagination(query=None, page=page, per_page=per_page,
                          total=len(photo_ids), items=photos)
    
    return render_template('main/search_semantic.html', 
                         q=q, photos=photos, pagination=pagination,
                         search_type='semantic')

# ===== ADD TRADITIONAL SEARCH WITH TOGGLE =====

@main_bp.route('/search')
def search():
    """Enhanced search with semantic option."""
    q = request.args.get('q', '').strip()
    mode = request.args.get('mode', 'keyword')  # keyword or semantic
    
    if not q:
        flash('Please enter a search query.', 'warning')
        return redirect(url_for('.index'))
    
    if mode == 'semantic':
        return redirect(url_for('.search_semantic', q=q))
    
    # Traditional keyword search (existing functionality)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ALBUMY_SEARCH_RESULT_PER_PAGE', 20)
    
    # Use existing Whoosh search if available
    pagination = Photo.query.whooshee_search(q).paginate(page, per_page)
    
    return render_template('main/search_semantic.html',
                         q=q, pagination=pagination,
                         photos=pagination.items,
                         search_type='keyword')

# ===== ADD FIND SIMILAR ROUTE =====

@main_bp.route('/photo/<int:photo_id>/similar')
def similar_photos(photo_id):
    """Option B: Find similar photos feature."""
    photo = Photo.query.get_or_404(photo_id)
    
    # Find similar photos using embeddings
    similar_ids = find_similar_photos(photo_id, limit=8)
    
    similar = []
    for pid in similar_ids:
        p = Photo.query.get(pid)
        if p and p.id != photo_id:
            similar.append(p)
    
    if not similar:
        flash('No similar photos found yet. Upload more photos to see similarities!', 'info')
    
    return render_template('main/similar.html',
                         photo=photo,
                         similar_photos=similar[:6])

# ===== ADD BATCH PROCESSING ROUTE (ADMIN) =====

@main_bp.route('/admin/generate-embeddings')
@login_required
@admin_required
def generate_embeddings():
    """Process existing photos to generate embeddings."""
    from albumy.semantic_ml import semantic_engine
    
    # Get photos without embeddings
    photos = Photo.query.filter(
        db.or_(Photo.embedding_vector == None, Photo.embedding_vector == '')
    ).limit(20).all()
    
    processed = 0
    for photo in photos:
        filepath = os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], photo.filename)
        if os.path.exists(filepath):
            try:
                embedding = integrate_with_upload(photo.id, filepath)
                photo.embedding_vector = json.dumps(embedding[:50])
                processed += 1
            except Exception as e:
                current_app.logger.error(f"Failed to process photo {photo.id}: {e}")
    
    db.session.commit()
    
    flash(f'Generated embeddings for {processed} photos.', 'success')
    return redirect(url_for('.index'))
