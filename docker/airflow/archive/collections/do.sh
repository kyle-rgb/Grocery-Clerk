
normalize_legacy_files(){
    7z x ./archive.7z ; 
    # find all gpg files in ./collections folder and ./nov_6 folder
    # move them to ../archive/collections
    # create parent directory for ./kroger in ./collections : mv ./collections/kroger ./collections/kroger/promotions both cashback and digital
    # move all folders with new structure from ./collections to ../archive/collections
    # ensure no clobber files on mv
    # delete ./collections
    # rename coupon folders to promotions
}

# one function that combines all gpg files together and re-encrypts is
combine_container_files(){
    # combine single gpg files down to one tar.gz file cat together
    declare -a files ; 
    declare file_name="$( date -I)_combined.tar.gz.gpg" ; 

    # decrypt files and make files
    for i in * ; do
        if [[ "$i" =~ .gpg$ ]]; then 
            echo "decrpyting $i"
            gpg -dq "$i"  > "${i/.gpg/}" ; 
            files+=("${i/.gpg}")
        fi ; 
    done ;

    # create combined tar and re-encrypt it 
    cat "${files[@]}" | gpg --output "./$file_name" --encrypt -r kylel9815@gmail.com  ;
    # remove intermediary files
    shred -u "${files[@]}" ;
    mv ./"$file_name" "../../../../data/" ;
    cd ../../../../data ;
    # add new files to archive for version control
    7z a ./archive.7z "./$file_name" -p -mhe ;
    # ls -F | grep -E "^[^s][^\/]+$" | tar -tvzif - | grep -e ^d
}


# gpg -d scraper_publix_promotions1_17_2023.tar.gz.gpg > pubP.tar.gz
# cat pubI.tar.gz pubP.yat.gz > combined.tar.gz
# tar -tvzif combined.tar.gz
# tar -xvzf combined.tar.gz