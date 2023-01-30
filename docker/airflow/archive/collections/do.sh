#! /bin/bash
normalize_legacy_files(){
    cd /m/gpg/archives/ ;
    7z x ./archive.7z;
    # find all gpg files in ./collections folder and ./nov_6 folder
    mv ./collections/nov_6/* ./collections ;
    rm -r ./collections/nov_6 ;
    # decrypt remaining gpg files in collections/ 
    for gpg_file in $(find collections/ -type f | grep -E "gpg$") ; do
        gpg -d "$gpg_file" | tar --strip=2 --transform='flags=r;s|\([0-9A-z_]\+\).json|'$(echo $gpg_file | sed -E "s|.*/(.*).tar.gz.gpg|\1.json|g")'|g' -xvzf - ;
        # mv -nv "$gpg_file" .. ; 
    done ;
    
    for i in ./archive/*/*/coupons; do 
        mv $i ${i/coupons/promotions} ; 
    done;
    # move them to ../archive/collections
    for folder in collections/*/*/ ; do
        if [[ -d "$folder" && ! "$folder" =~ "kroger" && ! "$folder" =~ "coupons" ]]; then 
            mv -nv /m/gpg/archives/${folder}* /m/gpg/archives/archive/${folder};
        elif [[ -d "$folder" && "$folder" =~ "coupons" ]]; then
            mv -nv /m/gpg/archives/${folder}* /m/gpg/archives/archive/${folder/coupons/promotions/};
        elif [[ -d "$folder" ]]; then
            mv -nv /m/gpg/archives/${folder}* /m/gpg/archives/archive/${folder/kroger\//kroger\/promotions/} ;
        fi;
    done; 
    
    # for gpg_folder in ./app/tmp/collections/*/; do 
    #     cp -vR "$gpg_folder" ./collections ;
    #     # find ./app/tmp/collections -type f -exec sh -c 'mv "$@" ./collections' sh {} + 
    # done ;
    
    # rm -r ./app ;


    # delete ./collections
    # rename coupon folders to promotions
}

# one function that combines all gpg files together and re-encrypts is
combine_container_files(){
    # check to see if new gpg files exists
    if [ "$( ls -A . | grep gpg$ )" ]; then
        mv -nv ./*.gpg /m/gpg ;
    else 
        echo "no new docker files to move" ;
    fi ;  

    
    cd /m/gpg/
    # combine single gpg files down to one tar.gz file cat together
    declare -a files ; 
    declare file_name="$( date -I)_combined.tar.gz" ;

    # decrypt files and make files
    for i in * ; do
        if [[ "$i" =~ .gpg$ ]]; then 
            echo "decrpyting $i"
            gpg -dq "$i"  >> "${i/.gpg}" ; 
            files+=("${i/.gpg}")
        fi ; 
    done ;

    # # create combined tar and re-encrypt it 
    cat "${files[@]}" | gpg --output "./$file_name.gpg" --encrypt -r kylel9815@gmail.com;
    # extract combined file into ./app/
    gpg -d "./$file_name.gpg" | tar -xvzif - ;
    # if ./archives/archive exists
    if [[ -e ./archives/archive ]]; then
        for gpg_file in ./archives/collections/*.gpg ; do
            local fn=${gpg_file/archives\/collections\//}
            gpg -dq "$gpg_file" >> ${fn/.gpg/} ; 
            mv -vn $gpg_file . ; 
            files+=(${fn/.gpg}) ; 
        done ;
        # move all files from ./archives/archive/collections into ./app/collections
        for original_file in ./archives/archive/collections/*/; do 
            cp -Rvn "$original_file" ./app/tmp/collections;
        done ;
    fi ;

    # move ./aldi/ ./app/tmp/collections/
    # move ./kroger/ ./app/tmp/collections
    # move ./app/tmp/collections/kroger/digital ./app/tmp/collections/kroger/promotions
    # move ./app/tmp/collections/kroger/cashback ./app/tmp/collections/kroger/promotions
    # then remove all these folders
    local move_folders=("aldi/" "kroger/" "app/tmp/collections/kroger/digital" "app/tmp/collections/kroger/cashback");
    for index in "${!move_folders[@]}" ; do
        if [[ $index -lt 2 ]] ; then 
            cp -Rvn ${move_folders[$index]} ./app/tmp/collections   
        elif [[ $index -eq 2 ]] ; then 
            cp -Rvn ${move_folders[$index]} ${move_folders[$index]/digital/promotions};
        elif [[ $index -eq 3 ]] ; then 
            cp -Rvn ${move_folders[$index]} ${move_folders[$index]/cashback/promotions} ;
        fi ;
        rm -rv ${move_folders[$index]} ;
    done ;
    # add all gpg files to separate archive
    # archive ./app/ 

    # # remove intermediary files
    tar -cvzf - "app/" | gpg --output "./${file_name}.gpg" --encrypt -r kylel9815@gmail.com;
    cat "${files[@]}" | gpg --output "./ALL_GPGs.tar.gz.gpg" --encrypt -r kylel9815@gmail.com;
    shred -u "${files[@]}" ;
    rm -r app/;
    echo "finalized archive files"

}

main() {
    normalize_legacy_files
    combine_container_files
}

main ; 

exit; 

# gpg -d scraper_publix_promotions1_17_2023.tar.gz.gpg > pubP.tar.gz
# cat pubI.tar.gz pubP.yat.gz > combined.tar.gz
# tar -tvzif combined.tar.gz
# tar -xvzf combined.tar.gz