declare -a files ; 
declare file_name="$( date -I)_combined.tar.gz.gpg" ; 

for i in * ; do
    if [[ "$i" =~ .gpg$ ]]; then 
        echo "decrpyting $i"
        gpg -dq "$i"  > "${i/.gpg/}" ; 
        files+=("${i/.gpg}")
    fi ; 
done ;

cat "${files[@]}" | gpg --output "./$file_name" --encrypt -r kylel9815@gmail.com  ;
rm "${files[@]}" ;
mv ./"$file_name" "../../../../data/" ;
cd ../../../../data ;
7z a ./archive.7z "./$file_name" -p -mhe ;
# gpg -d scraper_publix_promotions1_17_2023.tar.gz.gpg > pubP.tar.gz
# cat pubI.tar.gz pubP.yat.gz > combined.tar.gz
# tar -tvzif combined.tar.gz
# tar -xvzf combined.tar.gz