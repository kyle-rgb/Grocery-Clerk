#! /bin/bash
normalize_legacy_files(){
    cd /m/gpg/archives/ ;
    7z x ./archive.7z;
    # find all gpg files in ./collections folder and ./nov_6 folder
    mv ./collections/nov_6/* ./collections ;
    rm -r ./collections/nov_6 ;
    # decrypt remaining gpg files in collections/ 
    for gpg_file in $(find collections/ -type f | grep -E "gpg$") ; do
        gpg -d "$gpg_file" | tar -xvzf - ;
    done ;
    for gpg_folder in ./app/tmp/collections/*/; do 
        cp -vRT "$gpg_folder" ./collections ;
        # find ./app/tmp/collections -type f -exec sh -c 'mv "$@" ./collections' sh {} + 
    done ;
    
    for i in /m/gpg/archives/archive/*/*/coupons; do 
        mv $i ${i/coupons/promotions} ; 
    done;
    # move them to ../archive/collections
    for folder in collections/*/*/ ; do
        if [[ -d "$folder" && ! "$folder" =~ "kroger" ]]; then 
            mv -nv /m/gpg/archives/${folder}* /m/gpg/archives/archive/${folder};
        elif [[ -d "$folder" ]]; then
            mv -nv /m/gpg/archives/${folder}* /m/gpg/archives/archive/${folder/kroger\//kroger\/promotions/} ;
        fi;
    done; 
    
    
    # rm -r ./app ;


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

main() {
    normalize_legacy_files
}

main ; 

exit; 

# gpg -d scraper_publix_promotions1_17_2023.tar.gz.gpg > pubP.tar.gz
# cat pubI.tar.gz pubP.yat.gz > combined.tar.gz
# tar -tvzif combined.tar.gz
# tar -xvzf combined.tar.gz