export default async ({request})=>{
    const formData = await request.formData()
    const data = Object.fromEntries(formData)

    const isRegistered = await window.api.shortCut(data.shortCut)
    if (isRegistered){
        return window.api.sql(`update config set content=@content where id = 1`,
        'update',
        {
            content: JSON.stringify(data)
        }
    )
    }
   
    return {}
}